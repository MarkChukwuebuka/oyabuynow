// sales countdown timer

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".product-deal-timer").forEach(timer => {
        const startTime = new Date(timer.dataset.start).getTime();
        const endTime = new Date(timer.dataset.end).getTime();

        function updateCountdown() {
            const now = new Date().getTime();

            let targetTime, message;

            if (now < startTime) {
                // Sale hasn't started
                targetTime = startTime;
                message = "Sale Starts In";
            } else if (now >= startTime && now <= endTime) {
                // Sale is running
                targetTime = endTime;
                message = "Hurry up! Sale Ends In";
            } else {
                // Sale ended
                timer.querySelector(".product-title h4").textContent = "Sale Ended!";
                timer.querySelector(".days h5").textContent = "0";
                timer.querySelector(".hours h5").textContent = "0";
                timer.querySelector(".minutes h5").textContent = "0";
                timer.querySelector(".seconds h5").textContent = "0";
                clearInterval(interval);
                return;
            }

            const distance = targetTime - now;

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            timer.querySelector(".product-title h4").textContent = message;
            timer.querySelector(".days h5").textContent = days;
            timer.querySelector(".hours h5").textContent = hours;
            timer.querySelector(".minutes h5").textContent = minutes;
            timer.querySelector(".seconds h5").textContent = seconds;
        }

        updateCountdown();
        const interval = setInterval(updateCountdown, 1000);
    });
});
