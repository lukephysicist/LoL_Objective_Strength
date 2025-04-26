import * as funcs from './funcs'
// configure sliders
const timeSelectorDiv = document.querySelector('#time-selector') as HTMLDivElement;
const winprobSelectorDiv = document.querySelector('#winprob-selector') as HTMLDivElement;
funcs.configureSliders(timeSelectorDiv);
funcs.configureSliders(winprobSelectorDiv);

// configure rank buttons
const rankSelection = document.querySelector('#rank-selector') as HTMLElement;
const rankButtons = Array.from(rankSelection.querySelectorAll('button'));
rankButtons.forEach(button => {
    button.addEventListener('click', () =>{
        button.classList.toggle('active');
    });
});


// configure select all button
const selectAllButton = document.querySelector('#select-all-button') as HTMLButtonElement;

selectAllButton.addEventListener('click', () => {
    let allSelected = rankButtons.every(button => button.classList.contains('active'));

    rankButtons.forEach(button => {
        button.classList.toggle('active', !allSelected);
    });
});

// define request data
const minuteRange = (Array
                    .from(timeSelectorDiv.querySelectorAll('input'))
                    .map(input => input.value))

const winProbRange = (Array
                    .from(winprobSelectorDiv.querySelectorAll('input'))
                    .map(input => input.value))


const applyFiltersButton = document.querySelector('#apply-button') as HTMLButtonElement;
applyFiltersButton.addEventListener('click', () => {
    console.log(minuteRange)
    console.log(winProbRange)
})