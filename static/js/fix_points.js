let mimic_x_offset = 0,
    mimic_y_offset = 0,
    vertical_offset = 0,
    horizontal_offset = 0,
    point_radius = 7,
    COLORS = {1: 'blue', 2: 'red', 3: 'green', 4: 'white'};

$(window).on("load",function(){
    $("#progress_container").hide();
    load_parameters();
    let up_mouseButtonDown = false,
        down_mouseButtonDown = false,
        right_mouseButtonDown = false,
        left_mouseButtonDown = false;
    $("#up").on({
        'mousedown': () => up_mouseButtonDown = true,
        'mouseup': () => up_mouseButtonDown = false,
        'touchstart': () => up_mouseButtonDown = true,
        'touchend': () => up_mouseButtonDown = false
    });
    $("#down").on({
        'mousedown': () => down_mouseButtonDown = true,
        'mouseup': () => down_mouseButtonDown = false,
        'touchstart': () => down_mouseButtonDown = true,
        'touchend': () => down_mouseButtonDown = false
    });
    $("#right").on({
        'mousedown': () => right_mouseButtonDown = true,
        'mouseup': () => right_mouseButtonDown = false,
        'touchstart': () => right_mouseButtonDown = true,
        'touchend': () => right_mouseButtonDown = false
    });
    $("#left").on({
        'mousedown': () => left_mouseButtonDown = true,
        'mouseup': () => left_mouseButtonDown = false,
        'touchstart': () => left_mouseButtonDown = true,
        'touchend': () => left_mouseButtonDown = false
    });

    function animate(){
        if (up_mouseButtonDown) {
            let y = Number($("#mimic_offset_y").val());
            if (!isNaN(y)) {
                setTimeout(function () {
                    $("#mimic_offset_y").val(y - 1);
                    fix_points();
                }, 50)
            }
        }
        if (down_mouseButtonDown) {
            let y = Number($("#mimic_offset_y").val());
            if (!isNaN(y)){
                setTimeout(function () {
                    $("#mimic_offset_y").val(y + 1);
                    fix_points();
                }, 50)
            }
        }
        if (right_mouseButtonDown) {
            let x = Number($("#mimic_offset_x").val());
            if (!isNaN(x)){
                setTimeout(function () {
                    $("#mimic_offset_x").val(x + 1);
                    fix_points();
                }, 50)
            }
        }
        if (left_mouseButtonDown) {
                let x = Number($("#mimic_offset_x").val());
                if (!isNaN(x)){
                    setTimeout(function () {
                        $("#mimic_offset_x").val(x - 1);
                        fix_points();
                    }, 50)
                }
        }
        requestAnimationFrame(animate);
    }
    animate();

    let solve = $("#solve");
    solve.on('click', function () {
        solve[0].disabled = true;
        $("#parameters_form").hide();
        save_cookies();
        $("#progress_container").show();
        update_points_request();
    });
});

function paintOrder(order){
    $.ajax({
        type: "POST",
        url: "/paint_order",
        data: {'order': order, 'user_id': $("#user_id").val()},
        dataType: "json",
        encode: true,
        complete: function(xhr, textStatus) {
            if (xhr.status !== 200) {
                $("#error_button").trigger("click");
            }
        }
    }).done(function(data){
        if (data['success'] === true) {
            // reload image with order
            console.log(123123);
            let canvas = $("#canvas")[0],
                ctx = canvas.getContext("2d"),
                img = new Image();
            img.onload = function(){
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0, image_width, image_height);
            };
            img.src = filename + " order.png";
        }
        else
            $("#error_button").trigger("click");
    });
}
function update_points_request(){
    $.ajax({
        type: "POST",
        url: "/update_points",
        data: {'mimic_offset_x': $("#mimic_offset_x").val(),
            'mimic_offset_y': $("#mimic_offset_y").val(),
            'vertical_offset': $("#vertical_offset").val(),
            'horizontal_offset': $("#horizontal_offset").val(),
            'user_id': $("#user_id").val()},
        dataType: "json",
        encode: true,
        complete: function(xhr, textStatus) {
            if (xhr.status !== 200) {
                $("#error_button").trigger("click");
            }
        }
    }).done(function(data){
        if (data['success'] === true) {
            let index = 0;
            for (let flag of data['true_false_list']){
                if (flag === false)
                    $(`#_${index} .hexagon`).trigger('click');
                index += 1;
            }
            $("#calculate").trigger('click');
        }
        else
            $("#error_button").trigger("click");
    });
}

function save_cookies(){
    Cookies.set('mimic_x_offset', mimic_x_offset);
    Cookies.set('mimic_y_offset', mimic_y_offset);
    Cookies.set('vertical_offset', vertical_offset);
    Cookies.set('horizontal_offset', horizontal_offset);
    Cookies.set('point_radius', point_radius);
    Cookies.set('points_color', $("#point_color").val());
}
function drawImage(){
        let canvas = $("#canvas")[0],
            ctx = canvas.getContext("2d"),
            img = new Image(),
            point_color = COLORS[Number($("#point_color").val())];

        img.onload = function(){
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, image_width, image_height);
            for (const point of points){
                ctx.beginPath();
                let point_x = point[0] + mimic_x_offset + point[3]*horizontal_offset,
                    point_y = point[1] + mimic_y_offset + point[2]*vertical_offset;
                ctx.arc(point_x, point_y, point_radius, 0, 2 * Math.PI, false);
                ctx.fillStyle = point_color;
                ctx.fill();
            }
            $("#mimic_offset_x").val(mimic_x_offset);
            $("#mimic_offset_y").val(mimic_y_offset);
            $("#vertical_offset").val(vertical_offset);
            $("#horizontal_offset").val(horizontal_offset);
            $("#point_radius").val(point_radius);
        };
        img.src = filename;
    }
function fix_points(){
    let mimic_x_offset_input = $("#mimic_offset_x").val(),
        mimic_y_offset_input = $("#mimic_offset_y").val(),
        vertical_offset_input = $("#vertical_offset").val(),
        horizontal_offset_input = $("#horizontal_offset").val(),
        point_radius_input = $("#point_radius").val();

    if (!isNaN(mimic_x_offset_input) && !isNaN(mimic_y_offset_input) && !isNaN(vertical_offset_input)
        && !isNaN(horizontal_offset_input) && !isNaN(point_radius_input)){
        mimic_x_offset = Number(mimic_x_offset_input);
        mimic_y_offset = Number(mimic_y_offset_input);
        vertical_offset = Number(vertical_offset_input);
        horizontal_offset = Number(horizontal_offset_input);
        point_radius = Number(point_radius_input);
        drawImage();
    }
}
function load_parameters(){
    let x_cookie = Cookies.get('mimic_x_offset'),
        y_cookie = Cookies.get('mimic_y_offset'),
        vertical_cookie = Cookies.get('vertical_offset'),
        horizontal_cookie = Cookies.get('horizontal_offset'),
        radius_cookie = Cookies.get('point_radius'),
        point_color = Cookies.get('points_color');

    if (x_cookie && y_cookie && vertical_cookie && horizontal_cookie && radius_cookie && point_color) {
        mimic_x_offset = Number(x_cookie);
        mimic_y_offset = Number(y_cookie);
        vertical_offset = Number(vertical_cookie);
        horizontal_offset = Number(horizontal_cookie);
        point_radius = Number(radius_cookie);
        $("#point_color").val(point_color);
    }
    drawImage();
}
function reset_parameters(){
    mimic_x_offset = 0;
    mimic_y_offset = 0;
    vertical_offset = 0;
    horizontal_offset = 0;
    point_radius = 7;
    drawImage();
}