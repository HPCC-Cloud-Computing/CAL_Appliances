/**
 * Created by cong on 12/10/2017.
 */

let load_clusters_table = function (selector, table_name) {
    // console.log(selector);
    let clusterDataTable = $(selector).DataTable({
        "dom": '<"cluster-toolbar">frtip',
        responsive: true,
        "paging": false,
        "info": false,
        "autoWidth": false,
        "searching": true,
        "order": [[1, "desc"]],
        columns: [
            {data: 'id'},
            {data: 'name'},
            {data: 'address'},
            {data: 'storage_type'},
            {
                data: 'status',
                "render": function (data, type, row) {
                    if (data === 'ACTIVE') {
                        return '<span class="label label-primary">' + data + '</span>';

                    } else if (data === 'SHUTOFF') {
                        return '<span class="label label-danger">' + data + '</span>';

                    } else {
                        return data;
                    }

                }
            },
            {data: 'last_update'},
            {data: 'tbl_actions'}
        ]
    });
    $("div.cluster-toolbar").html('<h4 class="text-info">' + table_name + '</h4>');
    function updateClustersTable() {
        let tblElement = $(selector);
        $.ajax({
            method: "GET",
            data: {
                'ring_name': $(selector).data('ring-name'),
                'ring_version': $(selector).data('ring-version')
            },
            url: $(selector).data("get-clusters-api")
        })
            .done(function (clusters_data) {
                let cluster_list = clusters_data.cluster_list;
                for (let i = 0; i < cluster_list.length; i++) {
                    let cluster = cluster_list[i];
                    if (cluster.status === 1) {
                        cluster.status = 'ACTIVE';
                        // {#                                cluster.status_class = 'label label-primary'#
                        // }
                    } else if (cluster.status === 2) {
                        cluster.status = 'SHUTOFF';
                        // {#                                cluster.status_class = 'label label-warning'#
                        // }
                    }
                    cluster.storage_type = cluster.service_info.service_type;
                    cluster.address = cluster.address_ip + ":" + cluster.address_port;
                    cluster.tbl_actions = '1234';
                }
                clusterDataTable.clear();
                clusterDataTable.rows.add(cluster_list);
                clusterDataTable.draw();
            });
    }

    updateClustersTable();
    return setInterval(updateClustersTable, 4000);
};
