// alert_message('Success message', 'alert-success');
// alert_message('Danger message', 'alert-danger');
// alert_message('Info message', 'alert-info');

/**
 * Created by cong on 12/10/2017.
 */

let load_clusters_info_table = function (selector, table_name) {
    // console.log(selector);
    let clusterDataTable;

    if (!$.fn.DataTable.isDataTable(selector)) {
        clusterDataTable = $(selector).DataTable({
            "dom": '<"cluster-toolbar">frtip',
            responsive: true,
            "paging": false,
            "info": false,
            "autoWidth": false,
            "searching": true,
            "order": [[1, "desc"]],
            columns: [
                // {data: 'id'},
                {data: 'name'},
                {data: 'storage_type'},
                {data: "backend_type"},
                {data: 'capacity'},
                {data: 'Read10MB'},
                {data: 'Write10MB'},
                {data: 'Read128KB'},
                {data: 'Write128KB'},

                // {data: 'id'},
                // {data: 'name'},
                // {data: 'address'},
                // {data: 'storage_type'},
                // {
                //     data: 'status',
                //     "render": function (data, type, row) {
                //         if (data === 'ACTIVE') {
                //             return '<span class="label label-primary">' + data + '</span>';
                //
                //         } else if (data === 'SHUTOFF') {
                //             return '<span class="label label-danger">' + data + '</span>';
                //
                //         } else {
                //             return data;
                //         }
                //
                //     }
                // },
                // {data: 'last_update'},
                // {data: 'tbl_actions'}
            ]
        });
        $("div.cluster-toolbar").html('<h4 class="text-info">' + table_name + '</h4>');
    } else {
        // console.log('created!');
        clusterDataTable = $(selector).DataTable();
    }

    // console.log(query_param_obj);
    function updateClustersTable() {
        let clusterListApi = $(selector).data("cluster-list-api");
        $.ajax({
            method: "GET",
            url: clusterListApi
        })
            .done(function (clusters_data) {
                console.log(clusters_data);
                let cluster_list = clusters_data.cluster_list;
                for (let i = 0; i < cluster_list.length; i++) {
                    let cluster = cluster_list[i];
                    let clusterSpecs = JSON.parse(cluster.service_info.specifications);
                    console.log(cluster.service_info.specifications);
                    console.log(clusterSpecs);
                    cluster.storage_type = cluster.service_info.service_type;
                    cluster.backend_type = clusterSpecs["backend-type"];
                    cluster.capacity = clusterSpecs.capacity;
                    cluster.Read10MB = clusterSpecs["10mb-read"];
                    cluster.Write10MB = clusterSpecs["10mb-write"];
                    cluster.Read128KB = clusterSpecs["128k-read"];
                    cluster.Write128KB = clusterSpecs["128k-write"];

                }
                clusterDataTable.clear();
                clusterDataTable.rows.add(cluster_list);
                clusterDataTable.draw();
            });
    }

    updateClustersTable();
    // return setInterval(updateClustersTable, 4000);
};

function setDefineLimitOptions(formSelector) {
    let selectOptionSelector = $(formSelector).find("#select-option-name");
    let selected_option = $(selectOptionSelector).find(":selected").val();
    let capacityLimit = $(formSelector).find("input#capacity_limit");
    let read10mb_up = $(formSelector).find("input#read10mb_up");
    let write10mb_up = $(formSelector).find("input#write10mb_up");

    let read10mb_low = $(formSelector).find("input#read10mb_low");
    let write10mb_low = $(formSelector).find("input#write10mb_low");

    let read128k_up = $(formSelector).find("input#read128k_up");
    let write128k_up = $(formSelector).find("input#write128k_up");


    let read128k_low = $(formSelector).find("input#read128k_low");
    let write128k_low = $(formSelector).find("input#write128k_low");

    let submitButton = $(formSelector).find('#create-ring-submit-btn');


    if (selected_option.length === 0) {
        $(formSelector).find(".defined-option-input").each(function (index) {
            $(this).hide();
            submitButton.prop('disabled', true);

        });
    } else {
        submitButton.prop('disabled', false);
        $(formSelector).find(".defined-option-input").each(function (index) {
            $(this).show();
        });
        if (selected_option === 'optimize') {
            $("#upper_10mb").show();
            $("#lower_10mb").hide();
            $("#upper_128kb").show();
            $("#lower_128kb").hide();
            $(read10mb_up).val(1);
            $(write10mb_up).val(1);
            $(read128k_up).val(1);
            $(write128k_up).val(1);

            $(read10mb_low).val(1);
            $(write10mb_low).val(1);
            $(read128k_low).val(1);
            $(write128k_low).val(1);
        }

        if (selected_option === 'standard') {
            $("#upper_10mb").show();
            $("#lower_10mb").show();
            $("#upper_128kb").show();
            $("#lower_128kb").show();

            $(read10mb_up).val(1);
            $(write10mb_up).val(1);
            $(read128k_up).val(1);
            $(write128k_up).val(1);

            $(read10mb_low).val(1);
            $(write10mb_low).val(1);
            $(read128k_low).val(1);
            $(write128k_low).val(1);
        }
        if (selected_option === 'economy') {
            $("#upper_10mb").hide();
            $("#lower_10mb").show();
            $("#upper_128kb").hide();
            $("#lower_128kb").show();
            $(read10mb_up).val(1);
            $(write10mb_up).val(1);
            $(read128k_up).val(1);
            $(write128k_up).val(1);

            $(read10mb_low).val(1);
            $(write10mb_low).val(1);
            $(read128k_low).val(1);
            $(write128k_low).val(1);
        }
    }

}

function setupCreateDefinedForm(formSelector) {
    $("#select-option-name").on('change', function () {
        setDefineLimitOptions(formSelector);
        // console.log($("#select-option-name  :selected").val().length);
    });
    let formBodySelector = $(formSelector).find("#form-modal-body");

    let submitButton = $(formSelector).find('#create-ring-submit-btn');
    submitButton.on('click', function () {
        submitButton.prop('disabled', true);
        let optionName = $("select#select-option-name").find(":selected").val();
        let optionFullName = $("input#option-full-name").val();
        let optionDescription = $("input#option-description").val();
        let optionDuplicateFactor = $("input#duplicate-factor").val();
        let optionCapacityLimit = $("input#capacity-limit").val();

        let read10mb_up = $("input#read10mb_up").val();
        let write10mb_up = $("input#write10mb_up").val();

        let read10mb_low = $("input#read10mb_low").val();
        let write10mb_low = $("input#write10mb_low").val();

        let read128k_up = $("input#read128k_up").val();
        let write128k_up = $("input#write128k_up").val();

        let read128k_low = $("input#read128k_low").val();
        let write128k_low = $("input#write128k_low").val();

        $.ajax({
            type: "POST",
            data: {
                optionName: optionName,
                optionFullName: optionFullName,
                optionDescription: optionDescription,
                optionDuplicateFactor: optionDuplicateFactor,
                optionCapacityLimit: optionCapacityLimit,

                read10mb_up: read10mb_up,
                read10mb_low: read10mb_low,

                write10mb_up: write10mb_up,
                write10mb_low: write10mb_low,

                read128k_up: read128k_up,
                read128k_low: read128k_low,

                write128k_up: write128k_up,
                write128k_low: write128k_low,
            },
            url: $(formSelector).data("submit-url"),

            success: function (data) {
                // systemClusterTable.clear();
                // selectedClusterTable.clear();
                $(formBodySelector).modal('hide');

                if (data.create_result == 'true') {
                    setTimeout(function () {
                        alert_message('Create cluster ring successful!', 'alert-success');
                    }, 100);
                    setTimeout(function () {
                        location.reload();
                    }, 5000);
                } else if (data.create_result == 'false') {
                    setTimeout(function () {
                        alert_message(data.message, 'alert-danger');
                    }, 100);
                }
            },

            error: function (XMLHttpRequest, textStatus, errorThrown) {
                // systemClusterTable.clear();
                // selectedClusterTable.clear();
                $(formBodySelector).modal('hide');
                setTimeout(function () {
                    alert_message('Create cluster ring failed. Server Error!', 'alert-danger');
                }, 100);
            }
        });

    });
    $(formBodySelector).on('hidden.bs.modal', function () {
        console.log('destroyed!');
        // systemClusterTable.clear();
        // selectedClusterTable.clear();
    });
}

function initCreateClusterRingForm(formSelector) {
    setDefineLimitOptions(formSelector);
    load_clusters_info_table($(formSelector).find("#clusters-info-table"), 'Clusters Info');
    // let formSelector = $(formInfoSelector).closest(".create-cluster-ring-modal-form");
    let formBodySelector = $(formSelector).find("#form-modal-body");
    // console.log($(formSelector));
    $(formBodySelector).modal();
    // let clusterListApi = $(formSelector).data("cluster-list-api");

}

