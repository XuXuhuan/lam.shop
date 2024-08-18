const refMenuToggle = document.querySelector("#backButton");
const refBallValueCont = document.querySelector("#ballValueCont");
const refBallValueField = document.querySelector("#ballValueField");
const refDoubleValueButton = document.querySelector("#doubleValueButton");
const refHalfValueButton = document.querySelector("#halfValueButton");
function changeBallValue(multiplier) {
    if (isNaN(parseFloat(refBallValueField.value)) || parseFloat(refBallValueField.value) < 0) {
        refBallValueField.value = 0;
    } else {
        refBallValueField.value = Math.round(refBallValueField.value * multiplier * 100) / 100;
    }
}
refMenuToggle.addEventListener("click", function() {
    if (!refBallValueCont.classList.contains("hiddenCont")) {
        refBallValueCont.classList.add("hiddenCont");
        refMenuToggle.innerHTML = ">";
    } else {
        refBallValueCont.classList.remove("hiddenCont");
        refMenuToggle.innerHTML = "<";
    }
});
refDoubleValueButton.addEventListener("click", function () {changeBallValue(2)});
refHalfValueButton.addEventListener("click", function () {changeBallValue(0.5)});