import * as d3 from 'd3'

export function configureSliders(filterDiv: HTMLDivElement){
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


type RequestFormat = {
    minMinute: number;
    maxMinute: number;
    minProb: number;
    maxProb: number;
    ranks: (string | undefined)[];
};

export async function makeRequest(data: RequestFormat){
    try{
        const response = await fetch("http://localhost:8000/filter-request", {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if(!response.ok){
            throw new Error(`Request Error: ${response.status}`);
        }
        return response.json();
    } catch (error){
        console.log(error);
        return 'failure';
    }
}



export function drawDataViz(rawObjectiveData: Object){
    const objectiveData = (
                        Object.entries(rawObjectiveData)
                        .map(([objective, [mean, [lower, upper]]]) => 
                            ({
                            objective,
                            mean,
                            lower,
                            upper
                            })
                        )
    )
    // redraw svg
    const mainChartDiv = d3.select('#main-chart');
    const oldSVG = mainChartDiv.select('svg')
    if(oldSVG){
        oldSVG.remove();
    }

    const margin = {top: 20, right: 40, bottom: 40, left: 120};
    const width = 800 - margin.left - margin.right;
    const height = objectiveData.length * 50; // 50px per row

    const svgElement = mainChartDiv.append('svg')
                        .attr('width', width + margin.left + margin.right)
                        .attr("height", height + margin.top + margin.bottom)
                        .append('g')
                        .attr('transform', `translate(${margin.left},${margin.top})`)
    
    
}