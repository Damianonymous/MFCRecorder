window.onload = function() {
    for (element of document.getElementById("form").getElementsByTagName("input")) {
        element.addEventListener("change", function(event) { submitForm(); } );
    }
};

function submitForm() {
    console.log("submission");
    document.getElementById("form").submit();
}