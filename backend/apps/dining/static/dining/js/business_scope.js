(function () {
  function updateDependentOptions(dependent, businessField) {
    var selectedBusiness = businessField.value;
    Array.prototype.forEach.call(dependent.options, function (option) {
      if (!option.value) return;
      var matches = !selectedBusiness || option.dataset.businessId === selectedBusiness;
      option.hidden = !matches;
      option.disabled = !matches;
      if (!matches && option.selected) dependent.value = '';
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('[data-business-scope]'), function (dependent) {
      var businessField = document.getElementById('id_' + dependent.dataset.businessField);
      if (!businessField) return;
      var update = function () { updateDependentOptions(dependent, businessField); };
      businessField.addEventListener('change', update);
      update();
    });
  });
})();
