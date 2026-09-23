const glacierSelect = document.getElementById("glacier-select");

let temperatureChart = null;
let precipitationChart = null;
let selectedGlacierLayer = null;
let glacierLayersById = {};

<!-- map -->

const glacierMap = L.map("glacier-map").setView(
    [46.35, 8.0],
    9
);

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 18,
        attribution: "&copy; OpenStreetMap contributors"
    }
).addTo(glacierMap);

async function loadGlacierMap() {

    const response = await fetch("/glaciers/geojson");
    const geojson = await response.json();
	
	
	console.log(
    "GeoJSON features:",
    geojson.features.length
);
	
    const glacierLayer = L.geoJSON(
        geojson,
        {
            style: {
    color: "#1565c0",
    weight: 1,
    fillColor: "#42a5f5",
    fillOpacity: 0.45
},

            onEachFeature: function(feature, layer) {

				const properties = feature.properties;
				
				glacierLayersById[properties.rgi_id] = layer;

				const glacierName =
					properties.glac_name || "Unnamed Glacier";

				layer.bindTooltip(glacierName, {
					sticky: true
				});

				layer.on({

					mouseover: function(event) {

						const currentLayer = event.target;

						if (currentLayer !== selectedGlacierLayer) {
							currentLayer.setStyle({
								weight: 2,
								fillOpacity: 0.7
							});
						}
					},

					mouseout: function(event) {

						const currentLayer = event.target;

						if (currentLayer !== selectedGlacierLayer) {
							glacierLayer.resetStyle(currentLayer);
						}
					},

					click: function(event) {

						const currentLayer = event.target;
						const rgiId = properties.rgi_id;
						glacierSelect.value = rgiId;
						highlightGlacier(rgiId);



						loadGlacier(rgiId);
					}
				});
			}
        }
    ).addTo(glacierMap);

    glacierMap.fitBounds(
        glacierLayer.getBounds()
    );
}


function highlightGlacier(rgiId) {

    const layer = glacierLayersById[rgiId];

    if (!layer) {
        return;
    }

    if (selectedGlacierLayer) {
        selectedGlacierLayer.setStyle({
            color: "#1565c0",
            weight: 1,
            fillColor: "#42a5f5",
            fillOpacity: 0.45
        });
    }

    selectedGlacierLayer = layer;

    layer.setStyle({
        color: "#d32f2f",
        weight: 3,
        fillColor: "#ef5350",
        fillOpacity: 0.75
    });

    layer.bringToFront();

    glacierMap.fitBounds(
        layer.getBounds(),
        {
            padding: [40, 40],
            maxZoom: 12
        }
    );
}

<!-- map -->

async function loadGlaciers() {

    const response = await fetch("/glaciers");
    const data = await response.json();

    glacierSelect.innerHTML =
        '<option value="">Select a glacier</option>';

    data.glaciers.forEach(glacier => {

        const option = document.createElement("option");

        option.value = glacier.rgi_id;

        option.textContent =
            glacier.glac_name
                ? `${glacier.glac_name} — ${glacier.rgi_id}`
                : glacier.rgi_id;

        glacierSelect.appendChild(option);
    });
	
}


async function loadGlacier(rgiId) {

    const glacierResponse =
        await fetch(`/glaciers/${encodeURIComponent(rgiId)}`);

    const glacier = await glacierResponse.json();


    document.getElementById("glacier-name").textContent =
        glacier.glac_name || "Unnamed Glacier";

    document.getElementById("glacier-id").textContent =
        glacier.rgi_id;

    document.getElementById("area").textContent =
        `${Number(glacier.area_km2).toFixed(2)} km²`;

    document.getElementById("elevation").textContent =
        `${Number(glacier.dem_mean_m).toFixed(0)} m`;

    document.getElementById("relief").textContent =
        `${Number(glacier.dem_relief_m).toFixed(0)} m`;

    document.getElementById("glacier-details").style.display =
        "block";


    const climateResponse =
        await fetch(
            `/glaciers/${encodeURIComponent(rgiId)}/climate`
        );

    const climate = await climateResponse.json();
	

	const months = climate.climate.map(
		record => record.month
	);

	const temperatures = climate.climate.map(
		record => record.temperature_c
	);

	const precipitation = climate.climate.map(
		record => record.precipitation_mm
	);


	if (temperatureChart) {
		temperatureChart.destroy();
	}

	if (precipitationChart) {
		precipitationChart.destroy();
	}


	const temperatureContext =
		document
			.getElementById("temperature-chart")
			.getContext("2d");


	temperatureChart = new Chart(
		temperatureContext,
		{
			type: "line",

			data: {
				labels: months,

				datasets: [
					{
						label: "Temperature (°C)",
						data: temperatures,
						        borderColor: "#d32f2f",
								backgroundColor: "#d32f2f",
								pointBackgroundColor: "#d32f2f",
								pointBorderColor: "#d32f2f",
						tension: 0.25
					}
				]
			},

			options: {
				responsive: true,

				plugins: {
					legend: {
						display: true
					}
				},

				scales: {
					y: {
						title: {
							display: true,
							text: "Temperature (°C)"
						}
					},

					x: {
						title: {
							display: true,
							text: "Month"
						}
					}
				}
			}
		}
	);


	const precipitationContext =
		document
			.getElementById("precipitation-chart")
			.getContext("2d");


	precipitationChart = new Chart(
		precipitationContext,
		{
			type: "bar",

			data: {
				labels: months,

				datasets: [
					{
						label: "Precipitation (mm)",
						data: precipitation
					}
				]
			},

			options: {
				responsive: true,

				plugins: {
					legend: {
						display: true
					}
				},

				scales: {
					y: {
						beginAtZero: true,

						title: {
							display: true,
							text: "Precipitation (mm)"
						}
					},

					x: {
						title: {
							display: true,
							text: "Month"
						}
					}
				}
			}
		}
	);


	document.getElementById("charts-section").style.display =
		"block";
	
	
	
	
	
	

    const table =
        document.getElementById("climate-table");

    table.innerHTML = "";


    climate.climate.forEach(record => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${record.month}</td>
            <td>${record.temperature_c.toFixed(2)}</td>
            <td>${record.precipitation_mm.toFixed(2)}</td>
        `;

        table.appendChild(row);
    });


    document.getElementById("climate-section").style.display =
        "block";
}


glacierSelect.addEventListener("change", event => {

    const rgiId = event.target.value;

    if (rgiId) {
		highlightGlacier(rgiId);
        loadGlacier(rgiId);
    }
});


loadGlaciers();
loadGlacierMap();
