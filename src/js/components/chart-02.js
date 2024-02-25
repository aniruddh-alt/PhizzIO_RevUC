import ApexCharts from "apexcharts";

// ===== chartTwo
const chart02 = () => {
  const chartTwoOptions = {
    series: [
      {
        name: "Attended",
        data: [44, 55, 41, 49, 22, 43, 65],
      },
      {
        name: "Missed",
        data: [13, 23, 20, 19, 13, 27, 15],
      },
    ],
    colors: ["#3056D3", "#80CAEE"],
    chart: {
      type: "bar",
      height: 335,
      stacked: true,
      toolbar: {
        show: false,
      },
      zoom: {
        enabled: false,
      },
    },

    responsive: [
      {
        breakpoint: 1536,
        options: {
          plotOptions: {
            bar: {
              borderRadius: 0,
              columnWidth: "25%",
            },
          },
        },
      },
    ],
    plotOptions: {
      bar: {
        horizontal: false,
        borderRadius: 0,
        columnWidth: "35%",
        borderRadiusApplication: "end",
        borderRadiusWhenStacked: "last",
      },
    },
    dataLabels: {
      enabled: false,
    },

    xaxis: {
      categories: ["M", "T", "W", "T", "F", "S", "S"],
    },
    legend: {
      position: "top",
      horizontalAlign: "left",
      fontFamily: "Satoshi",
      fontWeight: 500,
      fontSize: "14px",

      markers: {
        radius: 99,
      },
    },
    fill: {
      opacity: 1,
    },
  };

  const chartSelector = document.querySelectorAll("#chartTwo");

  if (chartSelector.length) {
    const chartTwo = new ApexCharts(
      document.querySelector("#chartTwo"),
      chartTwoOptions
    );
    chartTwo.render();
  }
};

export default chart02;
