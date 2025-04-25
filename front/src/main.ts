import * as funcs from './funcs'

const timeSelectorDiv = document.querySelector('#time-selector') as HTMLDivElement;
const winprobSelectorDiv = document.querySelector('#winprob-selector') as HTMLDivElement;
funcs.configureSliders(timeSelectorDiv);
funcs.configureSliders(winprobSelectorDiv);