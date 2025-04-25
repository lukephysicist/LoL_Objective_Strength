const slider = document.querySelector(".range-slider") as HTMLElement;
const progress = slider?.querySelector(".progress") as HTMLElement;
// inputs boxes
const minMinuteInput = slider?.querySelector(".min-minutes") as HTMLInputElement;
const maxMinuteInput = slider?.querySelector(".max-minutes") as HTMLInputElement;
//sliders
const minInput = slider?.querySelector(".min-input") as HTMLInputElement;
const maxInput = slider?.querySelector(".max-input") as HTMLInputElement;

const updateProgress = () => {
    const minValue = parseFloat(minInput.value);
    const maxValue = parseFloat(maxInput.value);

    const range = Number(maxInput.max) - Number(minInput.min);
    const valueRange = Number(maxValue) - Number(minValue);

    // fraction of the bar displayed
    const width = valueRange / range * 100;
    // distance from the left edge in percent 
    const minOffset = ((minValue - Number(minInput.min)) / range) * 100;

    progress.style.width = width + "%";
    progress.style.left = minOffset + "%";

    minMinuteInput.value = String(minValue);
    maxMinuteInput.value = String(maxValue);
}

minInput.addEventListener('input', () => {
    if(parseFloat(minInput.value) >= parseFloat(maxInput.value)){
        maxInput.value = minInput.value;
    }
    updateProgress();
});

maxInput.addEventListener('input', () => {
    if(parseFloat(maxInput.value) <= parseFloat(minInput.value)){
        minInput.value = maxInput.value;
    }
    updateProgress()
});

minMinuteInput.addEventListener('input', () => {
    minInput.value = minMinuteInput.value;
    if(minMinuteInput.value >= maxMinuteInput.value){
        maxInput.value = minInput.value
    }
    updateProgress();
})

maxMinuteInput.addEventListener('input', () => {
    maxInput.value = maxMinuteInput.value
    if(maxMinuteInput.value <= minMinuteInput.value){
        minInput.value = maxInput.value
    }
    updateProgress();
})

updateProgress();