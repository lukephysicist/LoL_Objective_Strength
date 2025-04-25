function configureSliders(filterDiv: HTMLDivElement){
    const progress = filterDiv?.querySelector(".progress") as HTMLDivElement;
    // inputs boxes
    const minBoxInput = filterDiv?.querySelector(".min-box") as HTMLInputElement;
    const maxBoxInput = filterDiv?.querySelector(".max-box") as HTMLInputElement;
    //sliders
    const minSliderInput = filterDiv?.querySelector(".min-slider") as HTMLInputElement;
    const maxSliderInput = filterDiv?.querySelector(".max-slider") as HTMLInputElement;

    const updateProgress = () => {
        const minValue = parseFloat(minSliderInput.value);
        const maxValue = parseFloat(maxSliderInput.value);

        const range = Number(maxSliderInput.max) - Number(minSliderInput.min);
        const valueRange = Number(maxValue) - Number(minValue);

        // fraction of the bar displayed
        const width = valueRange / range * 100;
        // distance from the left edge in percent 
        const minOffset = ((minValue - Number(minSliderInput.min)) / range) * 100;

        progress.style.width = width + "%";
        progress.style.left = minOffset + "%";

        minBoxInput.value = String(minValue);
        maxBoxInput.value = String(maxValue);
    }

    minSliderInput.addEventListener('input', () => {
        if(parseFloat(minSliderInput.value) >= parseFloat(maxSliderInput.value)){
            maxSliderInput.value = minSliderInput.value;
        }
        updateProgress();
    });

    maxSliderInput.addEventListener('input', () => {
        if(parseFloat(maxSliderInput.value) <= parseFloat(minSliderInput.value)){
            minSliderInput.value = maxSliderInput.value;
        }
        updateProgress()
    });

    minBoxInput.addEventListener('input', () => {
        minSliderInput.value = minBoxInput.value;
        if(minBoxInput.value >= maxBoxInput.value){
            maxSliderInput.value = minSliderInput.value;
        }
        updateProgress();
    })

    maxBoxInput.addEventListener('input', () => {
        maxSliderInput.value = maxBoxInput.value
        if(maxBoxInput.value <= minBoxInput.value){
            minSliderInput.value = maxSliderInput.value;
        }
        updateProgress();
    })

    updateProgress();
}
const timeSelectorDiv = document.querySelector('#time-selector') as HTMLDivElement;
const winprobSelectorDiv = document.querySelector('#winprob-selector') as HTMLDivElement;
configureSliders(timeSelectorDiv);
configureSliders(winprobSelectorDiv);