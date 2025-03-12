$(document).ready(function () {
  let baseUrl = window.location.href.split('checklists')[0];

  // Store components as cached data
  window.appData = window.appData || {}; // Ensure it exists
  window.appData.componentData = components.flatMap((component) =>
    component.fields.map((field) => ({
      termLabel: field.label,
      termName: field.name,
      termId: `term-${field.name}`,
      descriptionText: field.description || 'No description available',
      componentLabel: component.group_label || '',
      componentId: `component-${component.group_name}`,
    }))
  );

  // Load values from the dropdowns
  // from the URL parameters
  setTimeout(loadSelectedValues, 100);

  // Load modals
  loadInfoModal();
  loadSearchModal();
  loadEmailModal();

  //  Tooltips initialisation
  initialiseTooltipsAndPopovers();

  // Click events
  $(document).on('click', '#infoModalLink', function (event) {
    event.preventDefault(); // Prevent the default link behavior

    // Close any open popovers before showing the modal
    $('[data-bs-toggle="popover"]').each(function () {
      const popover = bootstrap.Popover.getInstance(this); // Get popover instance
      if (popover) {
        popover.hide(); // Close the popover
      }
    });

    // Open the info modal
    $('#infoIconID').click(); // Assuming the modal has an id 'infoModal'
  });

  $('#download-manifest-btn').on('click', function (e) {
    e.preventDefault();

    let outputFileName = getOutputFileName();

    if (!outputFileName) {
      showWarningModal();
      return;
    }

    let standard = $('#std_dropdown').val();

    // Construct the spreadsheet file URL
    let downloadFileName = outputFileName.replace(/\.[^/.]+$/, '.xlsx');
    let downloadUrl = `${baseUrl}checklists/xlsx/${standard}/${downloadFileName}`;

    // Create a hidden <a> element to trigger the download
    let link = document.createElement('a');
    link.href = downloadUrl;
    link.download = downloadFileName;
    document.body.appendChild(link);
    link.click(); // Trigger the download
    document.body.removeChild(link);
  });

  // Change events
  // Attach event handlers to the dropdowns
  $('#std_dropdown, #tech_dropdown').on('change', function (e) {
    e.preventDefault(); // Prevent the default form submission

    let standard = $('#std_dropdown').val();
    let technology = $('#tech_dropdown').val();

    let currentParams = new URLSearchParams(window.location.search);
    let outputFileName = getOutputFileName();
    let selectedText = $(this).find('option:selected').text();

    $('#sub_btn').prop('disabled', false);
    $('#download-manifest-btn')
      .prop('disabled', false)
      .attr('title', 'Download blank manifest');

    // Update title attribute
    // $(this)
    //   .attr('title', selectedText) // Update title
    //   .attr('data-bs-original-title', selectedText); // Update Bootstrap's stored title

    // Reinitialise the tooltip
    let tooltipInstance = bootstrap.Tooltip.getInstance(this);
    if (tooltipInstance) {
      tooltipInstance.dispose(); // Remove existing tooltip
    }
    new bootstrap.Tooltip(this); // Create a new tooltip instance

    if (!outputFileName) {
      // Disable the download buttons if no valid output file is found
      $('#sub_btn').prop('disabled', true);
      $('#download-manifest-btn')
        .prop('disabled', true)
        .attr('title', 'No manifest to download');
      showWarningModal();
      return;
    }

    // Construct the file URL
    let targetUrl = `${baseUrl}checklists/html/${standard}/${outputFileName}`;
    let args = `?std_dropdown=${standard}&tech_dropdown=${technology}`;

    // Redirect to the target URL with the query parameters
    window.location.href = `${targetUrl}${args}`;
  });

  // Window events
  // Navigate to the top of the web page on button clicked
  let navigateToTopOfPageBtn = $('#navigateToTop');

  $(window).on('scroll', function () {
    if ($(window).scrollTop() > 100) {
      // Show 'scroll up' button
      navigateToTopOfPageBtn.addClass('show');
    } else {
      navigateToTopOfPageBtn.removeClass('show');
    }
  });

  navigateToTopOfPageBtn.on('click', function (e) {
    e.preventDefault();
    $('html, body').animate(
      {
        scrollTop: 0,
      },
      '300'
    );
  });
});

/*
 * Load the values of the dropdowns from the URL parameters
 *  and set them in the dropdowns.
 */

function loadSelectedValues() {
  let args = new URLSearchParams(window.location.search);

  // Set the value of the dropdown menu options
  // if it exists in the URL parameters
  function updateDropdown(selector, paramName) {
    let value = args.get(paramName);
    let $dropdown = $(selector);

    if (value !== null && $dropdown.find(`option[value="${value}"]`).length) {
      $dropdown.val(value);
    }

    // let selectedText = $dropdown.find('option:selected').text().trim();
    // if (selectedText) {
    //   $dropdown
    //     .attr('title', selectedText)
    //     .attr('data-bs-original-title', selectedText)
    //     .tooltip('dispose') // Dispose of the old tooltip
    //     .tooltip(); // Reinitialize Bootstrap tooltip
    // }
  }

  // Apply to both dropdowns
  updateDropdown('#std_dropdown', 'std_dropdown');
  updateDropdown('#tech_dropdown', 'tech_dropdown');
}

function getOutputFileName() {
  let standard = $('#std_dropdown').val();
  let technology = $('#tech_dropdown').val();

  for (let file in outputFileData) {
    let [tech, tech_label, std, std_label, version_desc] = outputFileData[file]; // Destructure tuple values
    if (tech === technology && std === standard) {
      return file; // Return the matched file
    }
  }
  return null;
}

// Function to populate the modal with outputFileData
function populateInfoModalContent() {
  let scInfoModalContent = '';
  let stxInfoModalContent = '';

  for (let key in outputFileData) {
    let [
      technology_name,
      technology_label,
      standard_name,
      standard_label,
      version_description,
    ] = outputFileData[key];

    let listItem = `<li><strong>${standard_label} & ${technology_label} (${technology_name}):</strong> ${version_description}</li>`;

    if (key.includes('sc_rnaseq')) {
      scInfoModalContent += listItem;
    } else if (key.includes('stx')) {
      stxInfoModalContent += listItem;
    }
  }

  // Insert data into the modal body (Ensure these IDs exist in info_modal.html)
  document.getElementById('singleCellInfoModalListID').innerHTML =
    scInfoModalContent;
  document.getElementById('stxInfoModalListID').innerHTML = stxInfoModalContent;
}

function loadInfoModal() {
  const infoIcon = document.getElementById('infoIconID');
  const modalContainer = document.getElementById('info-modal-container');

  if (!infoIcon) {
    console.error('Info icon not found!');
    return;
  }

  infoIcon.addEventListener('click', function (event) {
    event.preventDefault();

    // Load the modal HTML dynamically
    fetch('../../../../templates/info_modal.html')
      .then((response) => response.text())
      .then((data) => {
        modalContainer.innerHTML = data;
        // Wait for the modal to be added to the DOM
        requestAnimationFrame(() => {
          const modalElement = document.getElementById('infoModal');

          if (modalElement) {
            // Inject outputFileData into the modal
            populateInfoModalContent();

            const modal = new bootstrap.Modal(modalElement, {});
            modal.show();
          } else {
            console.error('Modal element not found in DOM.');
          }
        });
      })
      .catch((error) => console.error('Error loading modal:', error));
  });
}

function loadSearchModal() {
  const searchIcon = document.getElementById('searchIconID');
  const modalContainer = document.getElementById('search-modal-container');

  if (!searchIcon) {
    console.error('Error: Search icon not found!');
    return;
  }

  searchIcon.addEventListener('click', async function () {
    try {
      const response = await fetch('../../../../templates/search_modal.html');
      let modalHTML = await response.text();
      modalContainer.innerHTML = modalHTML;

      requestAnimationFrame(() => {
        const searchModalElement = document.getElementById('searchModal');
        if (!searchModalElement) {
          console.error('Error: Search modal not found.');
          return;
        }

        const searchModal = new bootstrap.Modal(searchModalElement, {});
        searchModal.show();

        // Ensure input elements exist before adding event listeners
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
          searchInput.addEventListener('click', () => searchModal.show());
        }

        // Auto-focus on search input when modal is shown
        searchModalElement.addEventListener('shown.bs.modal', function () {
          const searchQuery = document.getElementById('searchQuery');
          if (searchQuery) searchQuery.focus();
        });

        // Attach search functionality
        attachSearchFunctionality(searchModal, modalContainer);
      });
    } catch (error) {
      console.error('Error loading search modal:', error);
    }
  });
}

// Separate function to handle search logic
function attachSearchFunctionality(searchModal, modalContainer) {
  const searchQueryInput = document.getElementById('searchQuery');
  const searchResults = document.getElementById('searchResults');
  const totalMatches = document.getElementById('totalMatches');

  if (!searchQueryInput || !searchResults || !totalMatches) {
    console.error('Error: Search input or results container not found.');
    return;
  }

  searchQueryInput.addEventListener('input', function () {
    const query = this.value.toLowerCase().trim();
    searchResults.innerHTML = '';
    totalMatches.textContent = '';

    const items = modalContainer.querySelectorAll('#content .card');
    let matchCount = 0;

    // Exit early if query is empty
    if (query === '') return;

    const componentData = window.appData?.componentData || [];

    if (!Array.isArray(componentData) || componentData.length === 0) {
      console.error('Error: No component data available.');
      return;
    }

    console.log('componentData:', componentData);
    console.log('Is componentsData an array?:', Array.isArray(components));

    // Iterate over the components (fields) directly
    componentData.forEach((field) => {
      const termLabel = field.termLabel.toLowerCase();
      const termName = field.termName.toLowerCase();
      const termId = field.termId;
      const descriptionText = field.descriptionText.toLowerCase();
      const componentId = field.componentId;

      // Check if any of the fields' content matches the search query
      if (
        termLabel.includes(query) ||
        termName.toLowerCase().includes(query) ||
        descriptionText.includes(query)
      ) {
        matchCount++;

        // Create a list item for the search result
        const listItem = document.createElement('div');
        listItem.className =
          'list-group-item list-group-item-action search-result-item';

        const termLinkHeader = document.createElement('h1');
        termLinkHeader.className = 'search-result-header';
        termLinkHeader.textContent = 'Term: ';

        const termLink = document.createElement('a');
        termLink.href = `#${termId}`;
        termLink.className = 'text-primary search-result-link';
        termLink.textContent = field.termLabel;

        const componentBadge = document.createElement('span');
        componentBadge.className = 'badge bg-dark ms-auto fl-right';
        componentBadge.textContent = field.componentLabel; // Display the component label
        componentBadge.id = componentId;

        listItem.addEventListener('click', (event) => {
          event.preventDefault();
          searchModal.hide();
          searchQueryInput.value = '';
          searchResults.innerHTML = '';
          totalMatches.textContent = '';

          const targetAccordion = document.getElementById(componentId);

          if (targetAccordion) {
            const accordionItem = targetAccordion.closest('.accordion-item');
            const accordionButton =
              accordionItem?.querySelector('.accordion-button');

            if (accordionButton) {
              const isCollapsed =
                accordionButton.getAttribute('aria-expanded') === 'false';

              if (isCollapsed) {
                console.log('Expanding Accordion...'); // Debugging line
                // Expand the accordion
                accordionButton.click();

                // Wait for the collapse animation to finish before scrolling
                targetAccordion.addEventListener(
                  'shown.bs.collapse',
                  function scrollToTerm() {
                    const termElement = document.getElementById(termId);
                    console.log('Term Element:', termElement); // Debugging line
                    if (termElement) {
                      termElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                      });
                      console.log('Scrolling to term'); // Debugging line
                    }

                    // Remove event listener to avoid multiple triggers
                    targetAccordion.removeEventListener(
                      'shown.bs.collapse',
                      scrollToTerm
                    );
                  }
                );
              } else {
                console.log('Accordion already expanded'); // Debugging line
                // Accordion is already expanded, scroll immediately
                const termElement = document.getElementById(termId);
                if (termElement) {
                  termElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                  });
                }
              }
            }
          }
        });

        const description = document.createElement('p');
        description.className = 'mb-1 text-muted';
        description.textContent = field.descriptionText;

        termLinkHeader.appendChild(termLink);
        termLinkHeader.appendChild(componentBadge);
        listItem.appendChild(termLinkHeader);
        listItem.appendChild(description);
        searchResults.appendChild(listItem);
      }
    });

    // Get selected values from dropdowns
    let outputFileName = getOutputFileName();
    let selected_standard = $('#std_dropdown').val();
    let selected_technology = $('#tech_dropdown').val();

    // Display the selected filter criteria above the results
    $('#selectedStandard').text(selected_standard);
    $('#selectedTechnology').text(selected_technology);

    if (!outputFileName) {
      // Hide the searchCriteria div if no valid selections
      $('#searchCriteria').hide();
    }

    $('#searchCriteria').show();

    totalMatches.textContent =
      matchCount > 0 || outputFileName
        ? `${matchCount} matching items for selected filters`
        : `No matching items found for selected filters`;
  });
}

function initialiseTooltipsAndPopovers() {
  // Initialise tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl, {
      trigger: 'hover',
      placement: 'bottom',
    });
  });

  // Initialise popovers
  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  popoverTriggerList.map(function (popoverTriggerEl) {
    new bootstrap.Popover(popoverTriggerEl, {
      trigger: 'click',
      html: true,
      placement: 'top',
    });
  });
}

function loadEmailModal() {
  const emailIcon = document.getElementById('emailIconID');
  const modalContainer = document.getElementById('info-modal-container'); // You can rename this container if necessary.

  if (!emailIcon) {
    console.error('Email icon not found!');
    return;
  }

  emailIcon.addEventListener('click', function (event) {
    event.preventDefault();

    // Load the email modal HTML dynamically
    fetch('../../../../templates/email_modal.html')
      .then((response) => response.text())
      .then((data) => {
        modalContainer.innerHTML = data;

        // Wait for the modal to be added to the DOM
        requestAnimationFrame(() => {
          const modalElement = document.getElementById('emailModal');

          if (modalElement) {
            const modal = new bootstrap.Modal(modalElement, {});
            modal.show();
          } else {
            console.error('Modal element not found in DOM.');
          }
        });
      })
      .catch((error) => console.error('Error loading modal:', error));
  });
}

function showWarningModal() {
  const modalContainer = document.getElementById('warning-modal-container');

  if (!modalContainer) {
    console.error('Modal container not found!');
    return;
  }

  // Load the modal HTML dynamically
  fetch('../../../../templates/warning_modal.html')
    .then((response) => response.text())
    .then((data) => {
      modalContainer.innerHTML = data;

      // Wait for the modal to be added to the DOM and show it
      requestAnimationFrame(() => {
        const modalElement = document.getElementById('warningModal');
        if (modalElement) {
          const modal = new bootstrap.Modal(modalElement);
          modal.show();
        } else {
          console.error('Modal element not found in DOM.');
        }
      });
    })
    .catch((error) => console.error('Error loading error modal:', error));
}

function updateUrlWithParams() {
  // Get current query parameters from the URL
  let currentParams = new URLSearchParams(window.location.search);
  let standard = $('#std_dropdown').val();
  let technology = $('#tech_dropdown').val();

  currentParams.set('std_dropdown', standard);
  currentParams.set('tech_dropdown', technology);

  // Construct the new URL with only the query parameters
  let newUrl = '?' + currentParams.toString(); // Keep only the query parameters in the URL

  // Use history.pushState to update the URL without reloading the page
  history.pushState(null, '', newUrl);
}
