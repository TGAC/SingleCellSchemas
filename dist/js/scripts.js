$(document).ready(function () {
  let baseUrl = window.location.href.split('checklists')[0];

  // Call the function to load the values of the dropdowns from the URL parameters
  load_selects_values();

  // Attach a click event handler to the submit button
  $('#sub_btn').click(function (e) {
    e.preventDefault(); // Prevent the default form submission

    let standard = $('#std_dropdown').val();
    let technology = $('#tech_dropdown').val();
    let outputFileName = getOutputFileName();

    if (!outputFileName) {
      alert('No data available for the selected options.');
      return;
    }

    // Construct the file URL
    let targetUrl = `${baseUrl}checklists/html/${standard}/${outputFileName}`;
    let args = `?std_dropdown=${standard}&tech_dropdown=${technology}`;

    // Redirect to to the URL with query parameters
    window.location.href = targetUrl + args;
  });

  // Attach a click event handler to the download manifest button
  $('#download-manifest-btn').click(function (e) {
    e.preventDefault();

    let outputFileName = getOutputFileName();

    if (!outputFileName) {
      alert('No data available for the selected options.');
      return;
    }

    let standard = $('#std_dropdown').val();

    // Construct the spreadsheet file URL
    let downloadUrl = `${baseUrl}checklists/xlsx/${standard}/${outputFileName.replace(
      /\.[^/.]+$/,
      '.xlsx'
    )}`;

    // Create a hidden <a> element to trigger the download
    let link = document.createElement('a');
    link.href = downloadUrl;
    link.download = outputFileName;
    document.body.appendChild(link);
    link.click(); // Trigger the download
    document.body.removeChild(link);
  });
});
/*
* Load the values of the dropdowns from the URL parameters
*  and set them in the dropdowns.
*/
function load_selects_values() {
let args = new URLSearchParams(window.location.search);

// Set the value of the standard dropdown if it exists in the URL parameters
if (args.get('std_dropdown') !== null) {
    $('#std_dropdown').val(args.get('std_dropdown'));
}

// Set the value of the technology dropdown if it exists in the URL parameters
if (args.get('tech_dropdown') !== null) {
    $('#tech_dropdown').val(args.get('tech_dropdown'));
}
}

function getOutputFileName() {
let standard = $('#std_dropdown').val();
let technology = $('#tech_dropdown').val();

for (let file in outputFileData) {
    let [tech, std] = outputFileData[file]; // Destructure tuple values
    if (tech === technology && std === standard) {
    return file; // Return the matched file
    }
}
return null;
}