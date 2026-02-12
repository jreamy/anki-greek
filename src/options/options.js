

$deckOptions.then((options) => {
  options.addHtmlAddon(HTML_CONTENT, () => {
    const store = options.auxData();

    const prefix = "anki_greek"
    const defaults = {
      [`${prefix}_enabled`]: false,
      [`${prefix}_dialect`]: "Koine Greek",
      [`${prefix}_model_repo`]: "ilsp/Llama-Krikri-8B-Instruct-GGUF",
      [`${prefix}_model_filename`]: "*q4_k_m.gguf",
      [`${prefix}_verb_forms`]: "present infinitive\npresent active indicative"
    }

    const enabledInput = document.getElementById(`${prefix}_enabled`);
    const dialectInput = document.getElementById(`${prefix}_dialect`);
    const repoInput = document.getElementById(`${prefix}_model_repo`);
    const filenameInput = document.getElementById(`${prefix}_model_filename`);
    const verbFormsInput = document.getElementById(`${prefix}_verb_forms`);

    // update html when state changes
    store.subscribe((data) => {
      enabledInput.checked = data[`${prefix}_enabled`] ?? defaults[`${prefix}_enabled`];
      dialectInput.value = data[`${prefix}_dialect`] ?? defaults[`${prefix}_dialect`];
      repoInput.value = data[`${prefix}_model_repo`] ?? defaults[`${prefix}_model_repo`]
      filenameInput.value = data[`${prefix}_model_filename`] ?? defaults[`${prefix}_model_filename`]
      verbFormsInput.value = data[`${prefix}_verb_forms`] ?? defaults[`${prefix}_verb_forms`]
    });

    // update config when check state changes
    enabledInput.addEventListener("change", (_) =>
      store.update((data) => {
        return {
          ...defaults, ...data,
          [`${prefix}_enabled`]: enabledInput.checked,
        };
      })
    );
    dialectInput.addEventListener("change", (_) =>
      store.update((data) => {
        return {
          ...defaults, ...data,
          [`${prefix}_dialect`]: dialectInput.value,
        };
      })
    );
    repoInput.addEventListener("change", (_) => {
      return store.update((data) => {
        return {
          ...defaults, ...data,
          [`${prefix}_model_repo`]: repoInput.value,
        };
      });
    });
    filenameInput.addEventListener("change", (_) => {
      return store.update((data) => {
        return {
          ...defaults, ...data,
          [`${prefix}_model_filename`]: filenameInput.value,
        };
      });
    });
    verbFormsInput.addEventListener("change", (_) => {
      return store.update((data) => {
        return {
          ...defaults, ...data,
          [`${prefix}_verb_forms`]: verbFormsInput.value,
        };
      });
    });
  });
});