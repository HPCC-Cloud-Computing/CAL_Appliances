/**
 * Created by cong on 20/11/2017.
 */

$(document).ready(function () {
    $('[rel=tooltip]').tooltip({
        container: 'body',
        trigger: 'hover'
    });

    function loadContainersTable() {
        let containersTable = $('#containers-table').DataTable(
            {
                'createdRow': function (row, data, dataIndex) {
                    // console.log(data.name);
                    $(row).attr('data-container-name', data.info);
                },
                scrollY: '342px',
                scrollX: false,
                // scrollCollapse: true,
                paging: false,
                dom: 'lrtip',
                columns: [
                    {data: 'info'},
                ]
            }
        );

        function updateContainersTable() {
            let tblElement = $('#containers-table');
            let getContainerListApi = tblElement.data("container-list-api");
            $("#containers-filter").prop("disabled", true);
            $("#containers-table-loading .loading-info").html('Loading Container List...');
            $("#containers-table-loading").show();
            $.ajax({
                method: "GET",
                data: {},
                url: getContainerListApi
            })
                .done(function (data) {
                    // console.log(data);
                    let containersInfo = data.container_list;
                    let container_list = [];
                    for (let i = 0; i < containersInfo.length; i++) {
                        container_list.push({
                            'info': containersInfo[i]
                        });
                    }
                    setTimeout(function () {
                        containersTable.clear();
                        containersTable.rows.add(container_list);
                        containersTable.draw();
                        $("#containers-filter").prop("disabled", false);
                        $("#containers-table-loading").hide();
                    }, 100);
                });
        }

        updateContainersTable();

        // loading container info when click to a container in table
        $('#containers-table').on('click', 'tbody tr', function () {
            // console.log($(this).data('container-name'));

            if ($(this).hasClass('selected')) {
                // $(this).removeClass('selected');
                // $(this).find('td').html($(this).data('container-name').toString());
            }
            else {

                // show loading screens in containers table and files table
                $("#containers-filter").prop("disabled", true);
                $("#containers-table-loading .loading-info").html('Loading Container Information...');
                $("#containers-table-loading").show();

                $("#files-filter").prop("disabled", true);
                $("#files-table-loading .loading-info").html('Loading File Object List...');
                $("#files-table-loading").show();


                let selectedRow = this;
                let tblElement = $('#containers-table');
                let getContainerInfoApi = tblElement.data("container-info-api");
                $.ajax({
                    method: "GET",
                    data: {'container_name': $(this).data('container-name').toString()},
                    url: getContainerInfoApi
                })
                    .done(function (data) {
                        setTimeout(function () {
                            // console.log(data);
                            // push data for container selected row
                            let containerInfo = data.container_info;
                            let containerInfoHtml = $('#container-info-soure').html();
                            let containerInfoBox = $('<td/>').html(containerInfoHtml);
                            containerInfoBox.find("#container-name").html(containerInfo.name);
                            containerInfoBox.find("#object-count").html(containerInfo.object_count);
                            containerInfoBox.find("#container-size").html(containerInfo.size);
                            containerInfoBox.find("#date-created").html(containerInfo.date_created);
                            // console.log(containerInfoBox);
                            $(selectedRow).empty();
                            $(selectedRow).append(containerInfoBox);
                            let prevSelectedRow = containersTable.$('tr.selected');
                            if (prevSelectedRow.length !== 0) {
                                // console.log(selectedRow);
                                prevSelectedRow.find('td')
                                    .html($(prevSelectedRow).data('container-name').toString());
                                containersTable.$('tr.selected').removeClass('selected');
                            }
                            $(selectedRow).addClass('selected');

                            // push data for files table
                            // console.log(containerInfo);
                            let objectList = containerInfo.object_list;
                            let filesTable = $('#files-table').DataTable();
                            filesTable.clear();
                            filesTable.rows.add(objectList);
                            filesTable.draw();

                            // turnoff loading screens

                            $("#containers-filter").prop("disabled", false);
                            $("#containers-table-loading").hide();
                            $("#files-filter").prop("disabled", false);
                            $("#files-table-loading").hide();
                        }, 100);

                    });

            }
        });
        // Event listener to the two range filtering inputs to redraw on input
        $('#containers-filter').keyup(function () {
            containersTable.draw();
        });
    }

    loadContainersTable();

    // console.log($('#files-table'));
    let filesTable = $('#files-table').DataTable(
        {
            columnDefs: [
                {
                    orderable: false,
                    className: 'select-checkbox',
                    targets: 0,
                    "data": null,
                    "defaultContent": ''
                },
                {
                    "className": "btn-center",
                    "width": "20%", "targets": -1,
                    "orderable": false,
                    "data": function (row, type, val, meta) {
                        // console.log(row);
                        // console.log(val);
                        let fileActions = $("#file-actions-source").html();
                        let fileActionsBox = $(fileActions);
                        fileActionsBox.attr('data-object-name', row.file_name);
                        // console.log(fileActionsBox.prop('outerHTML'));
                        // return "<button>Edit</button>";
                        return fileActionsBox.prop('outerHTML');
                    }
                },
                {"data": "file_name", "targets": 1},
                {"data": "last_update", "targets": 2},
                {"data": "size", "targets": 3},
            ],
            'createdRow': function (row, data, dataIndex) {
                // console.log(data.name);
                $(row).attr('data-file-name', data.file_name);
            },
            // columns: [
            //     // {data: ''},
            //     // {data: 'file_name'},
            //     // {data: 'last_update'},
            //     // {data: 'file_size'},
            //     // {data: ''},
            // ],
            select: {
                style: 'multi',
                selector: 'tr>td:nth-child(1), tr>td:nth-child(2)'
            },
            order: [[1, 'asc']],
            'paging': true,
            'lengthChange': false,
            dom: 'lrtip',
            'ordering': true,
            'info': true,
            'autoWidth': true,
            "pageLength": 9
            // "pageLength": 9
        }
    );
    $('#files-filter').keyup(function () {
        console.log($(this).val());
        filesTable.search($(this).val()).draw();
    });

    // $('#containers-filter').keyup(function () {
    //     // console.log($(this).val());
    //     // containersTable.search($(this).val()).draw();
    // });

    /* Custom filtering function which will search data in column four between two values */
    $.fn.dataTable.ext.search.push(
        function (settings, data, dataIndex) {
            if (settings.nTable.id === "containers-table") {
                let searchKey = $('#containers-filter').val();
                let containerName = $(settings.aoData[dataIndex].nTr).data('container-name').toString();
                // console.log(containerName);// change (2)
                return containerName.indexOf(searchKey) >= 0;
            }
            else if (settings.nTable.id === "files-table") {
                let searchKey = $('#files-filter').val();
                let fileName = $(settings.aoData[dataIndex].nTr).data('file-name').toString();
                // console.log(fileName);// change (2)
                return fileName.indexOf(searchKey) >= 0;
            }
            else {
                return true;
            }
            // let min = parseInt( $('#min').val(), 10 );
            // var max = parseInt( $('#max').val(), 10 );
            // var age = parseFloat( data[3] ) || 0; // use data for the age column
            // return true;
            // if ( ( isNaN( min ) && isNaN( max ) ) ||
            //      ( isNaN( min ) && age <= max ) ||
            //      ( min <= age   && isNaN( max ) ) ||
            //      ( min <= age   && age <= max ) )
            // {
            //     return true;
            // }
            // return false;
        }
    );
    let table = $('#example').DataTable();

    function validContainerName() {
        let inputContainerName = $("#input-container-name").val();
        let validator = new RegExp("^[^/^_]+$");
        if (validator.test(inputContainerName)) {
            $("#input-container-name-valid-helper").removeClass("text-danger");
            $("#input-container-name-valid-helper").addClass("text-success");
            $("#input-container-name-form-group").removeClass("has-error");
            $("#create-container-submit-btn").prop('disabled', false);
        } else {
            $("#input-container-name-valid-helper").addClass("text-danger");
            $("#input-container-name-valid-helper").removeClass("text-success");
            $("#input-container-name-form-group").addClass("has-error");
            $("#create-container-submit-btn").prop('disabled', true);
        }
    }

    $("#create-container-btn").on('click', function () {
        $('#create-container-modal').modal();
        $("#input-container-name").val("");
        validContainerName();
    });
    $("#input-container-name").keyup(function () {
        validContainerName();

    });
    $("#create-container-submit-btn").on('click', function () {
        let inputContainerName = $("#input-container-name").val();
        console.log(inputContainerName);
        $('#create-container-modal').modal('hide');

    });
});

