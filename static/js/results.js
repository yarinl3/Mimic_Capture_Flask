let intervals = [];

function init_results(){
    let width = (window.innerWidth > 0) ? window.innerWidth : screen.width;
    if (width > 500)
        $("#result-div").width("500px");
    else
        $("#result-div").width((width-20).toString() + "px");

    for (let i=0; i < blocks_sets_length; i++){
        $(`#get_order-${i}`).on("click", function(){
            $(`#get_order-${i}`).hide();
            $(`#loading-${i}`).show();
            $.ajax({
                type: "POST",
                url: "/get_order",
                data: {
                    'user_id': $("#user_id").val(),
                    'benefit': $("#benefit").val(),
                    'blocks-set-number': i,
                },
                dataType: "json",
                encode: true,
                complete: function(xhr, textStatus) {
                    if (xhr.status !== 200) {
                        $("#error_button").trigger("click");
                    }
                }
            });
            let interval_order_results = setInterval(function(){check_order_result_results(i)}, 15000);
            intervals.push(interval_order_results);
        })
    }
    for (let i=0; i < blocks_sets_length; i++){
        $(`#loading-${i}`).hide();
    }
}

function check_order_result_results(i){
    $.ajax({
        type: "POST",
        url: "/check_order_result",
        data: {'user_id': $("#user_id").val(),
            'blocks-set-number': i},
        dataType: "json",
        encode: true,
        complete: function(xhr, textStatus) {
            if (xhr.status !== 200) {
                clearInterval(intervals[i]);
                $("#error_button").trigger("click");
            }
        }
    }).done(function(data){
        if (data['order_status'] === true){
            clearInterval(intervals[i]);
            let loading = $(`#loading-${i}`);
            if (data['found'] === true){
                $(`#image-${i}`).attr({src: data['image_path']});
                loading.text("Done");
            }
            else{
                this.$DoneDiv = $('<div style="text-align: -moz-center;"><div class="alert alert-danger" style="width: 30%" role="alert">No order found</div></div>');
                loading.after(this.$DoneDiv);
                loading.hide();
            }
        }
    });
}
