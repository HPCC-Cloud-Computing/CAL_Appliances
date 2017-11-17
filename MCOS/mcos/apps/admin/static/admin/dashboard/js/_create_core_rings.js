// alert_message('Success message', 'alert-success');
// alert_message('Danger message', 'alert-danger');
// alert_message('Info message', 'alert-info');


function initCreateClusterRingForm(formInfoSelector) {

    // console.log($(formInfoSelector));
    function updateClustersTable(clusterTable) {

    }

    let formSelector = $(formInfoSelector).closest(".create-cluster-ring-modal-form");
    let formBodySelector = $(formSelector).find("#form-modal-body");

    let submitButton = $(formBodySelector).find('#create-ring-submit-btn');
    submitButton.prop('disabled', true);

    let systemClusterTableSelector = $(formBodySelector).find("#ring-system-clusters");
    let selectedClusterTableSelector = $(formBodySelector).find("#ring-selected-clusters");
    // console.log('recreated!');

    let systemClusterTable;

    if (!$.fn.DataTable.isDataTable(systemClusterTableSelector)) {
        // console.log('not created!');
        systemClusterTable =
            $(systemClusterTableSelector).DataTable({
                responsive: true,
                "paging": false,
                "info": false,
                "autoWidth": false,
                "searching": false,
                "order": [[1, "desc"]],
                columns: [
                    {data: 'name'},
                    {data: 'address'},
                    {data: 'storage_type'},
                ]
            });
        $(systemClusterTableSelector).find('tbody').on('click', 'tr', function () {
            console.log(this);
            if ($(this).hasClass('selected')) {
                console.log('has selected');

                $(this).removeClass('selected');
            }
            else {
                console.log('not has selected');
                $(systemClusterTableSelector).find('tr.selected').removeClass('selected');
                $(this).addClass('selected');
            }
        });

    } else {
        // console.log('created!');
        systemClusterTable = $(systemClusterTableSelector).DataTable();
    }

    let selectedClusterTable;
    if (!$.fn.DataTable.isDataTable(selectedClusterTableSelector)) {
        selectedClusterTable =
            $(selectedClusterTableSelector).DataTable({
                responsive: true,
                "paging": false,
                "info": false,
                "autoWidth": false,
                "searching": false,
                "order": [[1, "desc"]],
                columns: [
                    {data: 'name'},
                    {data: 'address'},
                    {data: 'storage_type'},
                ]
            });

        $(selectedClusterTableSelector).find('tbody').on('click', 'tr', function () {
            if ($(this).hasClass('selected')) {
                $(this).removeClass('selected');
            }
            else {
                $(selectedClusterTableSelector).find('tr.selected').removeClass('selected');
                $(this).addClass('selected');
            }
        });
    } else {
        selectedClusterTable = $(selectedClusterTableSelector).DataTable();
    }

    //init dataTable for system cluster talble and selected cluster table
    let clusterListApi = $(formInfoSelector).data("cluster-list-api");

    $.ajax({
        method: "GET",
        url: clusterListApi
    })
        .done(function (clusters_data) {
            let cluster_list = clusters_data.cluster_list;
            for (let i = 0; i < cluster_list.length; i++) {
                let cluster = cluster_list[i];
                cluster.storage_type = cluster.service_info.service_type;
                cluster.address = cluster.address_ip + ":" + cluster.address_port;
            }
            let totalRow = systemClusterTable.data().count();
            // console.log(totalRow);
            systemClusterTable.clear();
            systemClusterTable.rows.add(cluster_list);
            systemClusterTable.draw();
            selectedClusterTable.clear();
            selectedClusterTable.draw();


            // display modal form

            $(formBodySelector).modal();


        });


    $(formBodySelector).find("#move-cluster-right").on('click', function () {
        let selected_row = systemClusterTable.row('.selected');
        if (selected_row.length !== 0) {
            let selected_row_data = selected_row.data();
            selectedClusterTable.row.add({
                'name': selected_row_data.name,
                'address': selected_row_data.address,
                'storage_type': selected_row_data.storage_type,
                'id': selected_row_data.id,
            }).draw(false);
            selected_row.remove().draw(false);
            if (selectedClusterTable.rows().data().length >= 3) {
                submitButton.prop('disabled', false);
            }
        }
    });
    $(formBodySelector).find("#move-cluster-left").on('click', function () {
        let selected_row = selectedClusterTable.row('.selected');
        if (selected_row.length !== 0) {
            let selected_row_data = selected_row.data();
            systemClusterTable.row.add({
                'name': selected_row_data.name,
                'address': selected_row_data.address,
                'storage_type': selected_row_data.storage_type,
                'id': selected_row_data.id,
            }).draw(false);
            selected_row.remove().draw(false);
            if (systemClusterTable.rows().data().length < 3) {
                submitButton.prop('disabled', true);
            }
        }
    });


    let cluster_account = {};
    submitButton.on('click', function () {
        let selected_clusters = selectedClusterTable.rows().data();
        let totalClusters = selected_clusters.length;
        for (let i = 0; i < selected_clusters.length; i++) {
            cluster_account[i] = selected_clusters[i].id;
        }
        $.ajax({
            type: "POST",
            data: {
                ring_type:$(formInfoSelector).data("ring-type"),
                clusters: cluster_account,
                totalClusters: totalClusters
            },
            url: $(formInfoSelector).data("submit-url"),

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
        // when ajax create account ring request is done, hide modal and
        // show notification, then after 500 ms reload page
    });
    $(formBodySelector).on('hidden.bs.modal', function () {
        console.log('destroyed!');
        systemClusterTable.clear();
        selectedClusterTable.clear();
    });
}

