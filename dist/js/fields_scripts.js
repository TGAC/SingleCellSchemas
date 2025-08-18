$(document).ready(function () {
  let baseUrl = window.location.href.split('checklists')[0];

  // Load values from the dropdown menu
  loadSelectedValues();
  openAccordionFromHash();

  // Load modals
  handleModals();
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

    let standard = $('#stdDropdown').val();

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
  $('#stdDropdown, #techDropdown').on('change', function (e) {
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
  // Set the value of the dropdown menu options
  // if it exists in the URL parameters
  function updateDropdown(selector, paramName, defaultValue) {
    let urlParams = new URLSearchParams(window.location.search);
    let value = urlParams.get(paramName) || defaultValue;
    let $dropdown = $(selector);
    let option = `option[value="${value}"]`;

    if (value !== null && $dropdown.find(option).length) {
      $dropdown.val(value);
      $dropdown.attr('title', $dropdown.find(option).text());
    }
  }

  // Set dropdowns based on URL
  updateDropdown('#stdDropdown', 'stdDropdown', 'dwc');
  updateDropdown('#techDropdown', 'techDropdown', 'sc_rnaseq');

  // Update URL and rebuild content
  updateUrlWithParams();
  updateContentBasedOnSelection();

  // Open accordion if hash exists once new content is rendered
  const observer = new MutationObserver(() => {
    if (openAccordionFromHash()) {
      observer.disconnect();
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Handle navigation changes (e.g. back/forward navigation or a pasted URL)
  window.addEventListener('popstate', () => {
    // Reload dropdowns and content
    updateDropdown('#stdDropdown', 'stdDropdown', 'dwc');
    updateDropdown('#techDropdown', 'techDropdown', 'sc_rnaseq');
    updateContentBasedOnSelection();

    // Try to open the accordion after new content has loaded
    const obs = new MutationObserver(() => {
      if (openAccordionFromHash()) {
        obs.disconnect();
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
  });

  // Re-run when hash changes i.e when a user clicks an internal reference
  window.addEventListener('hashchange', openAccordionFromHash);
}

function getOutputFileName() {
  let standard = $('#stdDropdown').val();
  let technology = $('#techDropdown').val();

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
  const modalContainer = document.getElementById('info-modal-container');

  // Elements that can trigger the contact modal
  const infoTriggers = [
    document.getElementById('infoIconID'),
    document.getElementById('footerAboutID'),
  ];

  infoTriggers.forEach((trigger, index) => {
    if (!trigger) {
      console.warn(`Trigger element ${index + 1} not found!`);
      return;
    }
    // Attach click event to each trigger
    trigger.addEventListener('click', function (event) {
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
              console.error('Info modal element not found in DOM.');
            }
          });
        })
        .catch((error) => console.error('Error loading info modal:', error));
    });
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

function handleModals() {
  // Exclude automatically added 'aria-hidden="true"' in the modal
  // template for dynamically injected modals
  document.addEventListener('hide.bs.modal', function (event) {
    if (document.activeElement) {
      document.activeElement.blur();
    }
  });
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
  let selected_standard = $('#stdDropdown').val();
  let selected_technology = $('#techDropdown').val();

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
  const modalContainer = document.getElementById('info-modal-container');

  // Elements that can trigger the contact modal
  const emailTriggers = [
    document.getElementById('emailIconID'),
    document.getElementById('footerContactID'),
  ];

  // Attach click event to each trigger if it exists
  emailTriggers.forEach((trigger, index) => {
    if (!trigger) {
      console.warn(`Trigger element ${index + 1} not found!`);
      return;
    }

    trigger.addEventListener('click', function (event) {
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
              console.error('Email modal element not found in DOM.');
            }
          });
        })
        .catch((error) => console.error('Error loading email modal:', error));
    });
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
          console.error('Warning modal element not found in DOM.');
        }
      });
    })
    .catch((error) => console.error('Error loading error modal:', error));
}

function openAccordionFromHash() {
  // Open accordion based on hash
  const hash = decodeURIComponent(window.location.hash.slice(1));
  if (!hash) return false;

  function tryOpen() {
    // Expect a format like "component-xxxx&term-yyyy"
    const [accordionComponentId, accordionItemId] = hash.split('&');
    if (!accordionComponentId || !accordionItemId) return false;

    const component = document.getElementById(accordionComponentId);
    const term = document.getElementById(accordionItemId);
    if (!component || !term) return false;

    // Open/expand accordion if it is collapsed
    if (!component.classList.contains('show')) {
      const button =
        component.previousElementSibling?.querySelector('.accordion-button');
      const onShown = () => {
        term.scrollIntoView({ behavior: 'auto', block: 'start' });
        component.removeEventListener('shown.bs.collapse', onShown);
      };

      component.addEventListener('shown.bs.collapse', onShown, { once: true });
      button.click();
    } else {
      // Scroll instantly to the accordion item if accordion
      // if it is already opened/expanded
      term.scrollIntoView({ behavior: 'auto', block: 'start' });
    }
    return true;
  }

  // Try to open the accordion immediately
  if (tryOpen()) return true;

  // Observe the DOM for dynamically loaded content
  const observer = new MutationObserver(() => {
    if (tryOpen()) {
      observer.disconnect();
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });
  return false;
}

function updateUrlWithParams({ method = 'replace', preserveHash = true } = {}) {
  // Update URL with dropdown values
  // Get current query parameters from the URL
  // let currentParams = new URLSearchParams(window.location.search);

  // // Get the values from the dropdown menus
  // let standard = $('#stdDropdown').val();
  // let technology = $('#techDropdown').val();

  // currentParams.set('stdDropdown', standard);
  // currentParams.set('techDropdown', technology);

  // // Construct the new URL with only the query parameters
  // let newUrl = window.location.pathname + '?' + currentParams.toString();

  // // Use history.pushState to update the URL without reloading the page
  // history.pushState(null, '', newUrl);

  const url = new URL(window.location.href);

  // Get the values from the dropdown menus
  let standard = $('#stdDropdown').val();
  let technology = $('#techDropdown').val();

  url.searchParams.set('stdDropdown', standard);
  url.searchParams.set('techDropdown', technology);

  if (!preserveHash) url.hash = '';

  // Update URL with dropdown values with 'push' method and
  // 'history.pushState' without reloading the page
  // or use history.replaceState if replace method is used
  const fn = method === 'push' ? history.pushState : history.replaceState;
  fn.call(history, null, '', url.toString());
}

// Dynamically load and update content based on selected filters
function updateContentBasedOnSelection() {
  let selectedStandard = $('#stdDropdown').val();
  let selectedTechnology = $('#techDropdown').val();
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
                      field.regex
                        ? `<tr><td>Regex</td><td>${field.regex}</td></tr>`
                        : ''
                    }
                    ${
                      field.namespace
                        ? `
                          <tr><td>Namespace</td>
                          <td><a href="${field.reference || '#'}"
                              title="${field.reference || '#'}"
                              target="${
                                field.reference ? '_blank' : '_self'
                              }">${field.namespace}</a>
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

  initialiseUIComponents(); //  Reinitialise UI components
  updateUrlWithParams(); // Update the URL with selected parameters
  addMissingHrefToReferences(); // Add 'href' attribute link to missing references
  openAccordionFromHash(); // Open accordion based on URL hash
}

function addMissingHrefToReferences() {
  // Select all links inside the rows of the accordion table
  const links = document.querySelectorAll('tr td a');

  links.forEach((link) => {
    const href = link.getAttribute('href');
    const target = link.getAttribute('target');

    // If href link exists then, set it as the current page URL + component ID & term ID
    // for the accordion item
    if (href === '#' && target === '_self') {
      // Find the closest accordion-body to get its ID
      const accordionBody = link.closest('.accordion-body');
      if (accordionBody) {
        const accordionItem = link.closest('.card[id]');
        const component = link.closest('.accordion-collapse[id]');
        if (accordionItem && component) {
          const termId = accordionItem.id; // e.g. "term-study_id"
          const compId = component.id; // e.g. "component-study"

          link.href = `${
            window.location.href.split('#')[0]
          }#${compId}&${termId}`;
          link.title = link.href;
        }
      }
    }
  });
}
