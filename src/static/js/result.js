$(document).ready(function () {
  let root = $("#root");
  if (data.url !== null && data.url.length > 0) {
    let loading = $("<div id='loading'></div>").html("Checking...");
    loading.appendTo(root);
    $.post({
      url: data.api["get-status"],
      headers: {"X-CSRFToken": data.token},
      data: {"url": data.url},
      dataType: "json"
    })
      .done(getStatus)
      .fail(function () {
        root.append("Error: Bad request");
      })
      .always(function () {
        loading.html("Finish");
      })
  } else {
    root.append("No data");
  }

  function getStatus(resp) {
    console.log(resp);
    if (!resp["error"]) {
      root.append("Status OK");
      root.append(`<p>Time: ${resp["data"]["time"]}</p>`);
      $.post({
        url: data.api["parse-content"],
        headers: {"X-CSRFToken": data.token},
        data: {"url": data.url},
        dataType: "json"
      })
        .done(function (resp) {
          console.log(resp);
        })
    } else {
      root.append(`Error: ${resp["error"]}`);
    }
  }
})
