
let isOnBottom=true;
addEventListener("load", init);
function init() {

    let select=document.createElement("select");
    let top=document.createElement("option");
    let bottom=document.createElement("option");
    top.innerHTML="top";
    bottom.innerHTML="bottom";

    bottom.setAttribute("value","bottom");
    top.setAttribute("value","top");
    select.insertAdjacentElement("afterbegin", bottom);
    bottom.insertAdjacentElement("afterend", top);
    let imagesList=document.getElementById("images");
    imagesList.insertAdjacentElement("beforebegin", select);
    let images= imagesList.querySelectorAll("img");

    for(let i=0;i<images.length;i++){
        images[i].addEventListener("click", selectImage);
    }
    select.addEventListener("change",selectChange);
    select.style.position = "absolute";
    select.style.left = "50%";
    select.style.transform = "translate(-50%, -50%)";
}
function selectImage(e) {
    let bigImage=document.querySelector("#images img:nth-of-type(1)");
    let bigImgSrc=bigImage.src;
    bigImage.src=e.target.src;
    e.target.src=bigImgSrc;
}
function selectChange(){
    const image2 = document.querySelector("#images img:nth-of-type(2)");
    const image3 = document.querySelector("#images img:nth-of-type(3)");
    const image4 = document.querySelector("#images img:nth-of-type(4)");

    if (isOnBottom){
        image2.style.order = "4";
        image3.style.order = "5";
        image4.style.order = "6";
    } else {
        image2.style.order = "1";
        image3.style.order = "2";
        image4.style.order = "3";
    }
    isOnBottom=!isOnBottom;
}