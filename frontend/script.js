
//----------------------------//
//           GLOBALS          //
//----------------------------//
let timeFrame = "15m";
let timeFrameMinutes = 15;


async function fetchTrashData() {
    try {
        const params = { timeframe: timeFrame };
        const url = new URL("http://localhost:5000/trash_data");

        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

        const data = await fetch(url);
        // const response = await fetch('http://localhost:5000/trash_data');
        // const data = await response.json();
        console.log(data);
        return data;
    } catch (error) {
        console.error('Ошибка при получении данных:', error);
        return null;
    }
}

// --- Data Calculation Module ---
function calculateAverageTrash(data) {
    const totalTrash = data.reduce((sum, item) => sum + item.trash, 0);
    return totalTrash / data.length;
}

// --- Plotting Module ---
function plotTrashData(data) {
    const margin = { top: 20, right: 30, bottom: 40, left: 40 };
    const width = 640 - margin.left - margin.right;
    const height = 360 - margin.top - margin.bottom;

    const svg = d3
        .select('#chart')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3
        .scaleBand()
        .domain(data.map((d) => d.time))
        .range([0, width])
        .padding(0.1);

    const y = d3
        .scaleLinear()
        .domain([0, d3.max(data, (d) => d.trash)])
        .nice()
        .range([height, 0]);

    svg
        .append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .attr('class', 'axis');

    svg
        .append('g')
        .call(d3.axisLeft(y))
        .attr('class', 'axis');

    const line = d3
        .line()
        .x((d) => x(d.time) + x.bandwidth() / 2)
        .y((d) => y(d.trash));

    svg
        .append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', '#2c6e49')
        .attr('stroke-width', 5)
        .attr('d', line);

    const tooltip = d3.select('#tooltip');

    svg
        .selectAll('.dot')
        .data(data)
        .enter()
        .append('circle')
        .attr('class', 'dot')
        .attr('cx', (d) => x(d.time) + x.bandwidth() / 2)
        .attr('cy', (d) => y(d.trash))
        .attr('r', 7)
        .attr('fill', '#2c6e49')
        .on('mouseover', function (event, d) {
            tooltip
                .style('display', 'block')
                .html(`<strong>${d.time}</strong><br>Количество мусора: ${d.trash}`)
                .style('left', `${event.pageX + 5}px`)
                .style('top', `${event.pageY - 20}px`);
        })
        .on('mouseout', () => {
            tooltip.style('display', 'none');
        })
        .on('mousemove', (event) => {
            tooltip
                .style('left', `${event.pageX + 5}px`)
                .style('top', `${event.pageY - 20}px`);
        });
}


// --- Popup Module ---
function showPopupIfNeeded() {
    const popup = document.getElementById('popup');
    const popupMessage = document.getElementById('popup-message');
    const closePopup = document.getElementById('close-popup');
    const averageTrash = window.averageTrash;

    if (averageTrash > 3) {
        popupMessage.textContent = `Много мусора! Среднее количество мусора: ${averageTrash}`;
        popup.style.display = 'flex';
    }

    closePopup.addEventListener('click', () => {
        popup.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === popup) {
            popup.style.display = 'none';
        }
    });
};

const setup_buttons = () => {
    const select_button = (button) => {
        button.classList.add("time-button-selected")
    };

    const unselect_buttons = () => {
        timeButtons.forEach(button => { button.classList.remove("time-button-selected"); })
    };

    const timeButtons = document.querySelectorAll('.time-button');

    timeButtons.forEach(button => {
        if (button.getAttribute("data-time") == timeFrame) {
            select_button(button);
        }
        button.addEventListener('click', event => {
            unselect_buttons();
            select_button(event.target);
            timeFrame = event.target.getAttribute('data-time');
            switch (timeFrame) {
                case "5m":
                    timeFrameMinutes = 1;
                    break;
                case "15m":
                    timeFrameMinutes = 15;
                    break;
                case "30m":
                    timeFrameMinutes = 30;
                    break;
                case "1h":
                    timeFrameMinutes = 60;
                    break;
                case "1d":
                    timeFrameMinutes = 1440;
                    break;
            }
            update_plot();
        });
    });
};

const clearChart = () => {
    d3.select("#chart").selectAll("*").remove();
};

const update_plot = async () => {
    const resp = await fetchTrashData();


    const data = await resp.json();

    if (data && data.length > 0) {
        const averageTrash = calculateAverageTrash(data);
        window.averageTrash = averageTrash;
        console.log('Среднее количество мусора:', averageTrash);

        clearChart();

        plotTrashData(data);
        showPopupIfNeeded();
    }
    setTimeout(update_plot, timeFrameMinutes * 60000);
};

// --- Main Execution ---
document.addEventListener('DOMContentLoaded', async () => {
    setup_buttons();
    await update_plot();
});
