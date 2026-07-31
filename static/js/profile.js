// ===============================================
// DATAINSIGHT PROFILE PAGE
// ===============================================

document.addEventListener("DOMContentLoaded", () => {

    animateCards();

});


// ===============================================
// CARD ANIMATION
// ===============================================

function animateCards(){

    const elements = document.querySelectorAll(

        ".profile-card, .info-card, .logout-section"

    );

    elements.forEach((element,index)=>{

        element.style.opacity = "0";

        element.style.transform = "translateY(30px)";

        setTimeout(()=>{

            element.style.transition = "all .6s ease";

            element.style.opacity = "1";

            element.style.transform = "translateY(0px)";

        }, index * 180);

    });

}


// ===============================================
// BUTTON HOVER EFFECT
// ===============================================

document.querySelectorAll(

    ".dashboard-btn, .logout-btn"

).forEach(button=>{

    button.addEventListener("mouseenter",()=>{

        button.style.transition = ".3s";

    });

});


// ===============================================
// END OF FILE
// ===============================================