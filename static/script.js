document.addEventListener('DOMContentLoaded', function () {
    const imageInput = document.getElementById('imageInput');
    const croppedImage = document.getElementById('croppedImage');
    const croppedImageContainer = document.getElementById('croppedImageContainer');
    const cropButton = document.getElementById('cropButton');
    let cropper;

    imageInput.addEventListener('change', function () {
        const file = this.files[0];
        const reader = new FileReader();

        reader.onload = function (e) {
            const img = new Image();
            img.src = e.target.result;
            img.onload = function () {
                if (cropper) {
                    cropper.destroy();
                }
                croppedImage.src = '';
                croppedImage.onload = function () {
                    croppedImageContainer.style.display = 'block'; // Show the cropped image container
                    cropper = new Cropper(croppedImage, {
                        aspectRatio: NaN, // Free aspect ratio
                        viewMode: 2,
                        autoCropArea: 1,
                    });
                };
                croppedImage.src = img.src;
            };
        };

        reader.readAsDataURL(file);
    });

    cropButton.addEventListener('click', function () {
        const canvas = cropper.getCroppedCanvas();
        if (!canvas) {
            return;
        }
        canvas.toBlob(function (blob) {
            const formData = new FormData();
            formData.append('cropped_image', blob, 'cropped_image.jpg');

            fetch('/process_image', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    return response.blob();
                }
                throw new Error('Network response was not ok.');
            })
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'table.xlsx';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            })
            .catch(error => console.error('There was a problem with the fetch operation:', error));
        });
    });
});
