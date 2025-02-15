document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const fileInputContainer = document.getElementById('file-input-container');
    const videoPlayer = document.getElementById('video-player');
    const myVideo = document.getElementById('my-video');
    const graphImg = document.getElementById('graph-img'); // Получаем картинку
    const container_trash = document.querySelector('.container_trash');
    let videoURL = null;

    fileInputContainer.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            videoURL = URL.createObjectURL(file);
            setTimeout(() => {
                videoPlayer.style.display = 'block';
                myVideo.src = videoURL;
                myVideo.load();
                fileInputContainer.style.display = 'none';
                
                // Меняем изображение на graph2.png
                if (graphImg) {
                    graphImg.style.display = 'none';
                }
                
                container_trash.style.display = 'block';

            }, 1000);
        } else {
            videoURL = null;
        }
    });
});
















// document.addEventListener('DOMContentLoaded', () => {
//     const fileInput = document.getElementById('file-input');
//     const fileInputContainer = document.getElementById('file-input-container');
//     const loaderContainer = document.getElementById('loader-container');
//     const loaderWindow = document.getElementById('loader-window');
//     const videoPlayer = document.getElementById('video-player');
//     const myVideo = document.getElementById('my-video');
//     let videoURL = null;

//     fileInputContainer.addEventListener('click', () => {
//         fileInput.click();
//     });

//     fileInput.addEventListener('change', (event) => {
//         const file = event.target.files[0];
//         if (file) {
//             videoURL = URL.createObjectURL(file);
//             setTimeout(() => {
//                 videoPlayer.style.display = 'block';

//                 // Set the video source
//                 myVideo.src = videoURL;
//                 myVideo.load();
//                 fileInputContainer.style.display = 'none';
//             }, 1000);
//         } else {
//             videoURL = null;
//         }
//     });
// });

// function generateThumbnail(videoFile) {
//     const video = document.createElement('video');
//     video.src = URL.createObjectURL(videoFile);
//     video.muted = true; // Ensure video doesn't play audio
//     video.load();

//     video.addEventListener('loadeddata', () => {
//     const canvas = document.createElement('canvas');
//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;
//     const ctx = canvas.getContext('2d');
//     ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

//     const thumbnailDataURL = canvas.toDataURL('image/jpeg');
//     thumbnail.src = thumbnailDataURL;
//     thumbnailContainer.style.display = 'block';
//     });
// }