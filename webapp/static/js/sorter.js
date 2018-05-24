window.onload = function() {
    var headCells = document.getElementById("thead").children;
    for (i = 0; i < headCells.length; i++) {
        headCells[i].addEventListener("click", function (event) { orderRow(this); } );
    }
};

function orderRow(btn) {
    var orderCol = btn.getAttribute("data-name");
    //sort order, true for ascending
    var asc = !btn.classList.contains("ascending");

    //delete markers from previous sorting
    for (element of btn.parentElement.children) {
        element.classList.remove("descending", "ascending");
    }
    btn.classList.add(asc ? "ascending" : "descending");

    function getValue(row) {
        for (var i = 0; i < row.children.length; i++) {
            if (row.children[i].getAttribute("data-name") == orderCol) {
                var result = row.children[i].value;
                if (btn.getAttribute("data-type") == "int") {
                    result = parseInt(result);
                }
                else if (btn.getAttribute("data-type") == "str") {
                    result = result.toLowerCase();
                }
                else if (btn.getAttribute("data-type") == "bool"){
                    result = row.children[i].checked;
                }
                return result;
            }
        }
    }

    //compare differently depending on sort order
    function compare(a, b) {
        if (asc) {
            return a > b;
        }
        else {
            return a < b;
        }
    }

    body = document.getElementById("tbody");
    var rows = body.children;
    var i = 1;
    //insertionsort
    while (i < rows.length) {
        var j = i;
        while (j > 0 && compare(getValue(rows[j-1]), getValue(rows[j]))) {
            body.insertBefore(rows[j], rows[j - 1]);
            j -= 1;
        }
        i++;
    }
}