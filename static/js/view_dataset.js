// =====================================================
// DataInsight - View Dataset
// =====================================================

let dataset = [];
let filteredData = [];

let numericColumns = [];
let categoricalColumns = [];

let charts = {};

const COLORS = [

    "#6366F1",
    "#8B5CF6",
    "#3B82F6",
    "#06B6D4",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#EC4899",
    "#14B8A6",
    "#F97316"

];

// =====================================================
// PAGE LOAD
// =====================================================

window.onload = async () => {

    await loadDataset();

};

// =====================================================
// LOAD DATASET
// =====================================================

async function loadDataset(){

    try{

        const response = await fetch(

            `/dataset-data/${UPLOAD_ID}`

        );

        const json = await response.json();

        dataset = json.data || [];

        filteredData = [...dataset];

        numericColumns =

            json.numeric_columns || [];

        categoricalColumns =

            json.categorical_columns || [];

        createFilters();

        populateDropdowns();

        updateQualityScore();

        createCharts();

        createInsights();

        initialiseSearch();

    }

    catch(error){

        console.error(

            "Dataset Load Error",

            error

        );

    }

}

// =====================================================
// FILTERS
// =====================================================

function createFilters(){

    const container =

        document.getElementById(

            "filterContainer"

        );

    if(!container) return;

    container.innerHTML = "";

    categoricalColumns.forEach(column=>{

        const wrapper =

            document.createElement("div");

        const label =

            document.createElement("label");

        label.innerText = column;

        const select =

            document.createElement("select");

        select.dataset.column = column;

        select.innerHTML =

        `<option value="">All ${column}</option>`;

        const values =

        [...new Set(

            dataset.map(

                row=>row[column]

            )

        )];

        values.sort();

        values.forEach(value=>{

            select.innerHTML +=

            `<option value="${value}">

                ${value}

            </option>`;

        });

        select.onchange = applyFilters;

        wrapper.appendChild(label);

        wrapper.appendChild(select);

        container.appendChild(wrapper);

    });

}

// =====================================================
// DROPDOWNS
// =====================================================

function populateDropdowns(){

    const ids=[

        "lineColumnSelect",

        "histogramColumn",

        "distributionColumn",

        "boxColumn",

        "scatterX",

        "scatterY"

    ];

    ids.forEach(id=>{

        const select=

        document.getElementById(id);

        if(!select) return;

        select.innerHTML="";

        numericColumns.forEach(column=>{

            select.innerHTML+=

            `<option value="${column}">

                ${column}

            </option>`;

        });

        select.onchange=()=>{

            createCharts();

        };

    });

}

// =====================================================
// APPLY FILTERS
// =====================================================

function applyFilters(){

    filteredData=[...dataset];

    document.querySelectorAll(

        "#filterContainer select"

    ).forEach(select=>{

        if(select.value!==""){

            filteredData=

            filteredData.filter(

                row=>

                String(

                    row[select.dataset.column]

                )===select.value

            );

        }

    });

    document.getElementById(

        "rowsStat"

    ).innerText=

    filteredData.length;

    updateQualityScore();

    createCharts();

    createInsights();

}

// =====================================================
// RESET FILTERS
// =====================================================

document.getElementById(

    "resetFilters"

)?.addEventListener(

    "click",

    ()=>{

        document.querySelectorAll(

            "#filterContainer select"

        ).forEach(select=>{

            select.value="";

        });

        filteredData=[...dataset];

        document.getElementById(

            "rowsStat"

        ).innerText=

        dataset.length;

        updateQualityScore();

        createCharts();

        createInsights();

    }

);
// =====================================================
// DATASET QUALITY SCORE
// =====================================================

function updateQualityScore(){

    let missing = 0;

    filteredData.forEach(row=>{

        Object.values(row).forEach(value=>{

            if(

                value===null ||

                value==="" ||

                value==="NaN"

            ){

                missing++;

            }

        });

    });

    const unique = new Set(

        filteredData.map(

            row=>JSON.stringify(row)

        )

    );

    const duplicates =

        filteredData.length - unique.size;

    let score = 100;

    score -= duplicates * 2;

    score -= missing * 0.2;

    score = Math.max(0, Math.min(100, score));

    const scoreElement =

        document.getElementById("qualityScore");

    if(scoreElement){

        scoreElement.innerText =

            `${Math.round(score)}%`;

        if(score >= 80){

            scoreElement.style.color = "#22c55e";

        }

        else if(score >= 60){

            scoreElement.style.color = "#f59e0b";

        }

        else{

            scoreElement.style.color = "#ef4444";

        }

    }

}

// =====================================================
// TABLE SEARCH
// =====================================================

function initialiseSearch(){

    const search =

        document.getElementById(

            "tableSearch"

        );

    if(!search) return;

    search.addEventListener(

        "keyup",

        function(){

            const value =

                this.value.toLowerCase();

            const rows =

                document.querySelectorAll(

                    "table tbody tr"

                );

            rows.forEach(row=>{

                row.style.display =

                row.innerText

                .toLowerCase()

                .includes(value)

                ? ""

                : "none";

            });

        }

    );

}

// =====================================================
// DESTROY CHARTS
// =====================================================

function destroyCharts(){

    Object.values(charts).forEach(chart=>{

        if(chart){

            chart.destroy();

        }

    });

    charts = {};

}

// =====================================================
// DEFAULT CHART OPTIONS
// =====================================================

function defaultOptions(){

    return{

        responsive:true,

        maintainAspectRatio:false,

        plugins:{

            legend:{

                labels:{

                    color:"#ffffff"

                }

            }

        },

        scales:{

            x:{

                ticks:{

                    color:"#cbd5e1"

                },

                grid:{

                    color:"rgba(255,255,255,.05)"

                }

            },

            y:{

                ticks:{

                    color:"#cbd5e1"

                },

                grid:{

                    color:"rgba(255,255,255,.05)"

                }

            }

        }

    };

}

// =====================================================
// RANDOM COLORS
// =====================================================

function getColors(length){

    const colors=[];

    for(let i=0;i<length;i++){

        colors.push(

            COLORS[

                i % COLORS.length

            ]

        );

    }

    return colors;

}
// =====================================================
// CREATE ALL CHARTS
// =====================================================

function createCharts(){

    destroyCharts();

    if(filteredData.length===0){

        return;

    }

    createBarChart();

    createDoughnutChart();

    createLineChart();

    createHistogram();

    createDistributionChart();

    createBoxChart();

    createScatterChart();

}


// =====================================================
// BAR CHART
// =====================================================

function createBarChart(){

    if(

        categoricalColumns.length===0 ||

        numericColumns.length===0

    ){

        return;

    }

    const category = categoricalColumns[0];

    const numeric = numericColumns[0];

    const labels = [];

    const values = [];

    filteredData.forEach(row=>{

        labels.push(

            row[category]

        );

        values.push(

            Number(row[numeric]) || 0

        );

    });

    charts.bar = new Chart(

        document.getElementById("barChart"),

        {

            type:"bar",

            data:{

                labels:labels,

                datasets:[{

                    label:numeric,

                    data:values,

                    backgroundColor:getColors(values.length),

                    borderRadius:8,

                    borderWidth:0

                }]

            },

            options:defaultOptions()

        }

    );

}


// =====================================================
// DOUGHNUT CHART
// =====================================================

function createDoughnutChart(){

    if(categoricalColumns.length===0){

        return;

    }

    const column = categoricalColumns[0];

    const counts = {};

    filteredData.forEach(row=>{

        counts[row[column]] =

            (counts[row[column]] || 0) + 1;

    });

    charts.doughnut = new Chart(

        document.getElementById("doughnutChart"),

        {

            type:"doughnut",

            data:{

                labels:Object.keys(counts),

                datasets:[{

                    data:Object.values(counts),

                    backgroundColor:getColors(

                        Object.keys(counts).length

                    ),

                    borderWidth:2,

                    borderColor:"#121c33"

                }]

            },

            options:{

                responsive:true,

                maintainAspectRatio:false,

                plugins:{

                    legend:{

                        position:"bottom",

                        labels:{

                            color:"#ffffff",

                            padding:20

                        }

                    }

                }

            }

        }

    );

}


// =====================================================
// LINE CHART
// =====================================================

function createLineChart(){

    if(numericColumns.length===0){

        return;

    }

    const column =

        document.getElementById(

            "lineColumnSelect"

        ).value || numericColumns[0];

    charts.line = new Chart(

        document.getElementById("lineChart"),

        {

            type:"line",

            data:{

                labels:filteredData.map(

                    (_,index)=>index+1

                ),

                datasets:[{

                    label:column,

                    data:filteredData.map(

                        row=>Number(row[column])

                    ),

                    borderColor:"#6366F1",

                    backgroundColor:

                        "rgba(99,102,241,.2)",

                    fill:true,

                    tension:.4,

                    pointRadius:3,

                    pointHoverRadius:6

                }]

            },

            options:defaultOptions()

        }

    );

}
// =====================================================
// HISTOGRAM
// =====================================================

function createHistogram(){

    if(numericColumns.length===0) return;

    const column =
        document.getElementById("histogramColumn").value ||
        numericColumns[0];

    const values = filteredData
        .map(row => Number(row[column]))
        .filter(v => !isNaN(v));

    charts.histogram = new Chart(

        document.getElementById("histogramChart"),

        {

            type:"bar",

            data:{

                labels:values.map((_,i)=>i+1),

                datasets:[{

                    label:column,

                    data:values,

                    backgroundColor:"#3B82F6",

                    borderRadius:6

                }]

            },

            options:defaultOptions()

        }

    );

}


// =====================================================
// DISTRIBUTION CHART
// =====================================================

function createDistributionChart(){

    if(numericColumns.length===0) return;

    const column =
        document.getElementById("distributionColumn").value ||
        numericColumns[0];

    const values = filteredData
        .map(row=>Number(row[column]))
        .filter(v=>!isNaN(v));

    charts.distribution = new Chart(

        document.getElementById("distributionChart"),

        {

            type:"line",

            data:{

                labels:values.map((_,i)=>i+1),

                datasets:[{

                    label:column,

                    data:values,

                    borderColor:"#10B981",

                    backgroundColor:"rgba(16,185,129,.20)",

                    fill:true,

                    tension:.35,

                    pointRadius:2

                }]

            },

            options:defaultOptions()

        }

    );

}


// =====================================================
// BOX PLOT (Five Number Summary)
// =====================================================

function createBoxChart(){

    if(numericColumns.length===0) return;

    const column =
        document.getElementById("boxColumn").value ||
        numericColumns[0];

    let values = filteredData

        .map(row=>Number(row[column]))

        .filter(v=>!isNaN(v))

        .sort((a,b)=>a-b);

    if(values.length===0) return;

    const min = values[0];

    const max = values[values.length-1];

    const q1 =
        values[Math.floor(values.length*0.25)];

    const median =
        values[Math.floor(values.length*0.5)];

    const q3 =
        values[Math.floor(values.length*0.75)];

    charts.box = new Chart(

        document.getElementById("boxChart"),

        {

            type:"bar",

            data:{

                labels:[
                    "Minimum",
                    "Q1",
                    "Median",
                    "Q3",
                    "Maximum"
                ],

                datasets:[{

                    label:column,

                    data:[
                        min,
                        q1,
                        median,
                        q3,
                        max
                    ],

                    backgroundColor:[
                        "#6366F1",
                        "#8B5CF6",
                        "#22C55E",
                        "#F59E0B",
                        "#EF4444"
                    ],

                    borderRadius:8

                }]

            },

            options:defaultOptions()

        }

    );

}


// =====================================================
// SCATTER PLOT
// =====================================================

function createScatterChart(){

    if(numericColumns.length < 2) return;

    const xColumn =
        document.getElementById("scatterX").value ||
        numericColumns[0];

    const yColumn =
        document.getElementById("scatterY").value ||
        numericColumns[1];

    const points = filteredData

        .map(row=>({

            x:Number(row[xColumn]),

            y:Number(row[yColumn])

        }))

        .filter(point=>

            !isNaN(point.x) &&

            !isNaN(point.y)

        );

    charts.scatter = new Chart(

        document.getElementById("scatterChart"),

        {

            type:"scatter",

            data:{

                datasets:[{

                    label:`${xColumn} vs ${yColumn}`,

                    data:points,

                    pointBackgroundColor:"#8B5CF6",

                    pointRadius:5

                }]

            },

            options:defaultOptions()

        }

    );

}
// =====================================================
// AI INSIGHTS
// =====================================================

function createInsights(){

    const container =

        document.getElementById("insightsContainer");

    if(!container) return;

    container.innerHTML = "";

    const insights = [];

    // Dataset Size

    if(filteredData.length > 10000){

        insights.push(
            "📈 Large dataset detected. Suitable for advanced analytics and machine learning."
        );

    }
    else if(filteredData.length > 1000){

        insights.push(
            "📊 Medium-sized dataset with sufficient records for meaningful analysis."
        );

    }
    else{

        insights.push(
            "📋 Small dataset. Ideal for quick analysis and visualization."
        );

    }

    // Numeric Columns

    insights.push(

        `🔢 ${numericColumns.length} numeric column(s) detected.`

    );

    // Categorical Columns

    insights.push(

        `📁 ${categoricalColumns.length} categorical column(s) detected.`

    );

    // Missing Values

    let missing = 0;

    filteredData.forEach(row=>{

        Object.values(row).forEach(value=>{

            if(

                value===null ||

                value==="" ||

                value==="NaN"

            ){

                missing++;

            }

        });

    });

    if(missing===0){

        insights.push(

            "✅ Excellent data quality. No missing values detected."

        );

    }
    else{

        insights.push(

            `⚠ ${missing} missing values found. Cleaning is recommended.`

        );

    }

    // Duplicate Rows

    const unique = new Set(

        filteredData.map(

            row=>JSON.stringify(row)

        )

    );

    const duplicates =

        filteredData.length - unique.size;

    if(duplicates===0){

        insights.push(

            "✅ No duplicate rows detected."

        );

    }
    else{

        insights.push(

            `⚠ ${duplicates} duplicate rows detected.`

        );

    }

    // Numeric Statistics

    numericColumns.forEach(column=>{

        const values =

            filteredData

            .map(row=>Number(row[column]))

            .filter(value=>!isNaN(value));

        if(values.length===0) return;

        const average =

            values.reduce(

                (a,b)=>a+b,

                0

            ) / values.length;

        const minimum =

            Math.min(...values);

        const maximum =

            Math.max(...values);

        insights.push(

            `📊 ${column}: Average ${average.toFixed(2)}, Minimum ${minimum}, Maximum ${maximum}`

        );

    });

    // Display Insights

    insights.forEach(text=>{

        const card =

            document.createElement("div");

        card.className =

            "insight-card";

        card.innerHTML =

        `
            <i class="fa-solid fa-circle-check"></i>

            <span>${text}</span>
        `;

        container.appendChild(card);

    });

}

// =====================================================
// REFRESH EVERYTHING
// =====================================================

function refreshDashboard(){

    updateQualityScore();

    createCharts();

    createInsights();

}

// =====================================================
// WINDOW RESIZE
// =====================================================

window.addEventListener(

    "resize",

    ()=>{

        Object.values(charts).forEach(chart=>{

            if(chart){

                chart.resize();

            }

        });

    }

);

// =====================================================
// END OF FILE
// =====================================================