let tableData = [];

function loadCSV() {

    const fileInput = document.getElementById("csvFile");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select a CSV file.");
        return;
    }

    const reader = new FileReader();

    reader.onload = function(e) {

        const text = e.target.result;

        parseCSV(text);

    };

    reader.readAsText(file);

}

function parseCSV(text) {

    const rows = text.trim().split("\n");

    tableData = rows.map(row => row.split(","));

    displayTable();

    calculateStatistics();

}

function displayTable() {

    const table = document.getElementById("dataTable");

    table.innerHTML = "";

    tableData.forEach((row,index)=>{

        const tr = document.createElement("tr");

        row.forEach(cell=>{

            const element = document.createElement(index===0 ? "th":"td");

            element.textContent = cell;

            tr.appendChild(element);

        });

        table.appendChild(tr);

    });

}

function calculateStatistics(){

    const totalRecords = tableData.length - 1;

    const totalColumns = tableData[0].length;

    document.getElementById("records").innerHTML = totalRecords;
    document.getElementById("columns").innerHTML = totalColumns;

    let numbers=[];

    for(let i=1;i<tableData.length;i++){

        for(let j=0;j<tableData[i].length;j++){

            let value=parseFloat(tableData[i][j]);

            if(!isNaN(value)){

                numbers.push(value);

            }

        }

    }

    if(numbers.length>0){

        let max=Math.max(...numbers);

        let min=Math.min(...numbers);

        let sum=0;

        numbers.forEach(num=>sum+=num);

        let avg=(sum/numbers.length).toFixed(2);

        document.getElementById("maximum").innerHTML=max;
        document.getElementById("minimum").innerHTML=min;
        document.getElementById("average").innerHTML=avg;

    }

    document.getElementById("uploads").innerHTML=1;

}