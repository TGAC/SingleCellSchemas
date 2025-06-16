$(document).ready(function () {
  let baseUrl = window.location.href.split('checklists')[0];

  // Load values from the dropdown menu
  loadSelectedValues();

  // Load modals
  loadInfoModal();
  loadSearchModal();
  loadEmailModal();

  // Initialise UI components
  initialiseUIComponents();

  // Click events
  $('.dropdown-menu-info-icon').on('click', function (e) {
    e.stopPropagation(); // Prevent the event from bubbling up to the document

    // Close all other popovers before opening the new one
    $('.dropdown-menu-info-icon').not(this).popover('hide');

    // Toggle the clicked popover (show if hidden, hide if shown)
    $(this).popover('toggle');
  });

  // Close any open popovers when clicking anywhere else on the document
  $(document).on('click', function () {
    $('.dropdown-menu-info-icon').popover('hide');
  });

  $(document).on('click', '.info-modal-toc-link', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });

  $(document).on('click', '#infoModalLink', function (event) {
    event.preventDefault(); // Prevent the default link behaviour

    // Close any open popovers before showing the modal
    $('[data-bs-toggle="popover"]').each(function () {
      const popover = bootstrap.Popover.getInstance(this); // Get popover instance
      if (popover) {
        popover.hide(); // Close the popover
      }
    });

    // Open the info modal
    $('#infoIconID').click();
  });

  $(document).on('click', '#sampleInfoLink', function (event) {
    event.preventDefault(); // Prevent the default link behaviour

    // Close any open accordion items before showing the modal
    $('.accordion-collapse').each(function () {
      const collapse = bootstrap.Collapse.getInstance(this); // Get collapse instance
      if (collapse) {
        collapse.hide(); // Close the accordion item
      }
    });

    // Open the info modal
    $('#infoIconID').click();

    // Wait for modal to be visible (DOM updates after ~200ms)
    setTimeout(function () {
      const modal = document.getElementById('infoModal');
      const isVisible = modal && modal.classList.contains('show');

      if (isVisible) {
        const target = document.getElementById('sampleMetadataInfo');
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });

          // Add highlight class
          target.classList.add('highlight-flash');

          // Remove the class after animation completes
          setTimeout(() => {
            target.classList.remove('highlight-flash');
          }, 2000);
        }
      }
    }, 300); // Adjust if modal animates slowly (e.g., 300–500ms)
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
  // Attach event handlers to the dropdown menus
  $('#std_dropdown, #tech_dropdown').on('change', function (e) {
    e.preventDefault(); // Prevent the default form submission
    updateUrlWithParams();

    let outputFileName = getOutputFileName();
    let fieldsAccordion = $('#fieldsAccordion');

    $('#sub_btn').prop('disabled', false);
    $('#download-manifest-btn')
      .prop('disabled', false)
      .attr('title', 'Download blank manifest');

    if (!outputFileName) {
      // Disable the download button if no valid output file is found
      $('#sub_btn').prop('disabled', true);
      $('#download-manifest-btn')
        .prop('disabled', true)
        .attr('title', 'No manifest to download');

      fieldsAccordion.empty();
      fieldsAccordion.append(`
      <div class="accordion-item">
        <div class="accordion-header">
          <button class="accordion-button" type="button">
            No data found
          </button>
        </div>
      </div>
    `);
      showWarningModal();
      return;
    }

    // Update content based on the selected filters
    updateContentBasedOnSelection();
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

function loadSelectedValues() {
  let urlParams = new URLSearchParams(window.location.search);

  // Set the value of the dropdown menu options
  // if it exists in the URL parameters
  function updateDropdown(selector, paramName, defaultValue) {
    let value = urlParams.get(paramName) || defaultValue;
    let $dropdown = $(selector);

    if (value !== null && $dropdown.find(`option[value="${value}"]`).length) {
      $dropdown.val(value);
    }
  }

  // Apply to both dropdowns
  updateDropdown('#std_dropdown', 'std_dropdown', 'dwc');
  updateDropdown('#tech_dropdown', 'tech_dropdown', 'sc_rnaseq');
  updateUrlWithParams(); // Update the URL with the selected parameters
  updateContentBasedOnSelection();
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

    let listItem = `<li><strong>${standard_label} & ${technology_label}:</strong> ${version_description}</li>`;

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
    fetch(`${relPathTraverse}templates/info_modal.html`)
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
      const response = await fetch(
        `${relPathTraverse}templates/search_modal.html`
      );
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
          this.removeAttribute('aria-hidden');

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

function scrollToTerm(termId) {
  const termElement = document.getElementById(termId);
  if (termElement) {
    termElement.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });
  }
}

// Function to handle accordion expansion and scrolling
function handleAccordionExpand(termId, targetAccordion) {
  function scrollToTermWrapper() {
    scrollToTerm(termId);
    targetAccordion.removeEventListener(
      'shown.bs.collapse',
      scrollToTermWrapper
    );
  }

  const accordionItem = targetAccordion.closest('.accordion-item');
  const accordionButton = accordionItem?.querySelector('.accordion-button');
  const accordionCollapse = accordionItem?.querySelector('.accordion-collapse');

  if (accordionButton && accordionCollapse) {
    const isExpanded =
      accordionButton.getAttribute('aria-expanded') === 'true' &&
      accordionCollapse.classList.contains('show');

    if (isExpanded) {
      // Already expanded, scroll to term
      scrollToTerm(termId);
    } else {
      accordionButton.click(); // Expand accordion

      targetAccordion.addEventListener(
        'shown.bs.collapse',
        scrollToTermWrapper
      );
    }
  }
}

// Handle search logic
function attachSearchFunctionality(searchModal, modalContainer) {
  let outputFileName = getOutputFileName();
  const searchQueryInput = document.getElementById('searchQuery');
  const searchResults = document.getElementById('searchResults');
  const totalMatches = document.getElementById('totalMatches');

  if (!searchQueryInput || !searchResults || !totalMatches) {
    console.error('Error: Search input or results container not found.');
    return;
  }

  // Get selected values from dropdowns
  let selected_standard = $('#std_dropdown').val();
  let selected_technology = $('#tech_dropdown').val();

  if (!outputFileName) {
    $('#selectedStandard').text(selected_standard);
    $('#selectedTechnology').text(selected_technology);
    $('#searchCriteria').show();

    searchQueryInput.disabled = true;
    searchQueryInput.style.display = 'none';
    totalMatches.textContent = 'No matching items found for selected filters';
  }

  searchQueryInput.addEventListener('input', function () {
    const query = this.value.toLowerCase().trim();
    let matchCount = 0;
    searchResults.innerHTML = '';
    totalMatches.textContent = '';
    searchQueryInput.disabled = false;
    searchQueryInput.style.display = 'block';

    // Exit early if query is empty
    if (query === '') return;

    if (!Array.isArray(components) || components.length === 0) {
      console.error('Error: No component data available.');
      return;
    }

    // Iterate over the components (fields) directly
    components.forEach((component) => {
      const componentId = `component-${component.group_name}`;
      const componentLabel = component.group_label;

      component.fields.forEach((field) => {
        const termLabel = field.label.toLowerCase();
        const termName = field.name.toLowerCase();
        const termId = `term-${field.name}`;
        const descriptionText = field.description.toLowerCase();

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
          termLink.textContent = field.label;

          const componentBadge = document.createElement('span');
          componentBadge.className = 'badge bg-dark ms-auto fl-right';
          componentBadge.textContent = componentLabel;
          componentBadge.id = componentId;

          // Event listener for search results
          listItem.addEventListener('click', (event) => {
            event.preventDefault();
            searchModal.hide();
            searchQueryInput.value = '';
            searchResults.innerHTML = '';
            totalMatches.textContent = '';

            const targetAccordion = document.getElementById(componentId);

            if (targetAccordion) {
              handleAccordionExpand(termId, targetAccordion);
            }
          });

          const description = document.createElement('p');
          description.className = 'mb-1 text-muted';
          description.textContent = field.description;

          termLinkHeader.appendChild(termLink);
          termLinkHeader.appendChild(componentBadge);
          listItem.appendChild(termLinkHeader);
          listItem.appendChild(description);
          searchResults.appendChild(listItem);
        }
      });
    });

    // Display the selected filter criteria above the results
    $('#selectedStandard').text(selected_standard);
    $('#selectedTechnology').text(selected_technology);

    $('#searchCriteria').show();

    totalMatches.textContent =
      matchCount > 0 || outputFileName
        ? `${matchCount} matching items for selected filters`
        : 'No matching items found for selected filters';
  });
}

function initialiseUIComponents() {
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
    fetch(`${relPathTraverse}templates/email_modal.html`)
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
  fetch(`${relPathTraverse}templates/warning_modal.html`)
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

  // Get the values from the dropdown menus
  let standard = $('#std_dropdown').val();
  let technology = $('#tech_dropdown').val();

  currentParams.set('std_dropdown', standard);
  currentParams.set('tech_dropdown', technology);

  // Construct the new URL with only the query parameters
  let newUrl = window.location.pathname + '?' + currentParams.toString();

  // Use history.pushState to update the URL without reloading the page
  history.pushState(null, '', newUrl);
}

// Dynamically load and update content based on selected filters
function updateContentBasedOnSelection() {
  let selectedStandard = $('#std_dropdown').val();
  let selectedTechnology = $('#tech_dropdown').val();
  let fieldsAccordion = $('#fieldsAccordion');

  // Filter components based on standardName and technologyName
  let filteredComponents = components.filter((item) => {
    return (
      item.standard_name === selectedStandard &&
      item.technology_name === selectedTechnology
    );
  });

  // Empty the current accordion content
  fieldsAccordion.empty();

  if (filteredComponents.length) {
    // Iterate over the filtered components and dynamically add them to the accordion
    filteredComponents.forEach(function (component) {
      let accordionItem = `
      <div class="accordion-item">
        <div class="accordion-header">
          <button class="accordion-button" type="button" data-bs-toggle="collapse" 
            data-bs-target="#component-${component.group_name}" 
            aria-expanded="true"
            aria-controls="component-${component.group_name}">${
        component.group_label
      }
            <!-- Show info note only if group_label is "Sample" -->
            ${
              component.group_label === 'Sample'
                ? `
              <div class="info-note text-muted">
                <i class="fa fa-info-circle sample-info-icon"></i>Why is only partial metadata shown? 
                <a id="sampleInfoLink" href="#">Learn more</a>.
              </div>
            `
                : ''
            }
          </button>
        </div>
        <div id="component-${component.group_name}" 
          class="accordion-collapse collapse" data-bs-parent="#fieldsAccordion">
          <div class="accordion-body">
          ${component.fields
            .map(
              (field) => `
              <div id="term-${field.name}" class="card">
                <h5 class="card-header d-flex align-items-start">
                  ${field.label}
                  ${
                    field.mandatory === 'mandatory'
                      ? `<span class="badge bg-dark ms-auto">Required</span>`
                      : ''
                  }
                </h5>
                <div class="card-body">
                  <table class="table">
                    <tr><td>Name</td><td>${field.name}</td></tr>
                    <tr><td>Description</td><td>${field.description}</td></tr>
                    ${
                      field.example
                        ? `<tr><td>Example</td><td>${field.example}</td></tr>`
                        : ''
                    }
                    ${
                      field.reference
                        ? `
                          <tr><td>Reference</td><td>
                              <a href="${field.reference}" target="_blank">${field.reference}</a>
                          </td></tr>`
                        : ''
                    }
                    ${
                      field.regex
                        ? `<tr><td>Regex</td><td>${field.regex}</td></tr>`
                        : ''
                    }
                    ${
                      field.namespace
                        ? `
                          <tr><td>Namespace</td><td>
                              ${
                                field.reference
                                  ? `<a href="${field.reference}" target="_blank">${field.namespace}</a>`
                                  : field.namespace
                              }
                          </td></tr>`
                        : ''
                    }
                    ${
                      field.allowedValues && field.allowedValues.length > 0
                        ? `
                          <tr><td>Allowed Values</td><td>
                              ${field.allowedValues
                                .map(
                                  (value) =>
                                    `<span class="badge bg-dark">${value}</span>`
                                )
                                .join(' ')}
                          </td></tr>`
                        : ''
                    }
                  </table>
                </div>
              </div>
            `
            )
            .join('')}
          </div>
        </div>
      </div>`;

      // Append the dynamically created accordion item
      fieldsAccordion.append(accordionItem);
    });
  }
  //  Reinitialise UI components
  initialiseUIComponents();
  updateUrlWithParams(); // Update the URL with the selected parameters
}
