/**
 * Created by cong on 12/10/2017.
 */

let load_clusters_table = function (selector,table_name) {
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
    $("div.cluster-toolbar").html('<h4 class="text-info">'+table_name+'</h4>');

    let cluster_ids_str = $(selector).data('cluster-ids');
    let cluster_ids = cluster_ids_str.split(":");
    let total_cluster_ids = cluster_ids.length;
    let query_param_obj = {'cluster_id_number': total_cluster_ids};
    for (let i = 0; i < total_cluster_ids; i++) {
        query_param_obj['cluster_id_' + i.toString()] = cluster_ids[i];

    }
    // console.log(query_param_obj);
    function updateClustersTable() {
        let tblElement = $(selector);
        let getClusterWithIdsApi = tblElement.data("get-clusters-ids-api");

        $.ajax({
            method: "GET",
            data: query_param_obj,
            url: getClusterWithIdsApi
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
