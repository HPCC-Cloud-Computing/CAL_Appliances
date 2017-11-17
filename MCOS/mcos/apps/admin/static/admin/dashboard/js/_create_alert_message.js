/**
 * Created by cong on 12/10/2017.
 */

function alert_message(message_content, alert_class_type) {

    let alert_element = jQuery('<div/>', {
        // id: 'foo',
        class: "alert alert-dismissable " + alert_class_type,
        rel: 'external',
    })
        .append($('<a href="#" class="close" data-dismiss="alert" aria-label="close">×</a>'))
        .append(message_content)
        .appendTo($("#alert-message-box"));
    setTimeout(function () {
        alert_element.fadeOut("normal", function () {
            $(this).remove();
        });
    }, 10000);

    // <div class="alert alert-success alert-dismissable">
    //     <a href="#" class="close" data-dismiss="alert" aria-label="close">×</a>
    //     Create account ring successful!
    // </div>
}