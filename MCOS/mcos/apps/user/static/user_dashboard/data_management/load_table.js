/**
 * Created by cong on 20/11/2017.
 */

$(document).ready(function () {
    $('[rel="tooltip"]').tooltip({
        container: 'body',
        trigger: 'hover'
    });
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
            ],
            "language": {
                "emptyTable": "No container available"
            },
        }
    );
    // containersTable.select.style( 'api' );
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
                {
                    "data": "last_update", "targets": 2,
                    "render": function (data, type, row) {
                        console.log(data);
                        return data;
                        // if (data === 'ACTIVE') {
                        //     return '<span class="label label-primary">' + data + '</span>';
                        //
                        // } else if (data === 'SHUTOFF') {
                        //     return '<span class="label label-danger">' + data + '</span>';
                        //
                        // } else {
                        //     return data;
                        // }
                    }
                },
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


    function loadContainersTable() {
        let tblElement = $('#containers-table');
        let getContainerListApi = tblElement.data("container-list-api");
        $("#containers-filter").prop("disabled", true);
        $("#containers-table-loading .loading-info").html('Loading Container List...');
        $("#containers-table-loading").show();

        $("#files-filter").prop("disabled", true);
        $("#files-table-loading .loading-info").html('Loading File Object List...');
        $("#files-table-loading").show();

        $.ajax({
            method: "GET",
            data: {},
            url: getContainerListApi
        })
            .done(function (data) {
            })
            .fail(function (jqXHR, textStatus, error) {
                // Handle error here
                alert_message(
                    'Failed to retrieval container list. Reason: ' + textStatus,
                    'alert-danger');
            })
            .always(function (data) {
                let container_list = [];
                if (data.result === 'success') {
                    let containersInfo = data.container_list;
                    for (let i = 0; i < containersInfo.length; i++) {
                        container_list.push({'info': containersInfo[i]});
                    }
                } else if (data.result === 'failed') {
                    alert_message(
                        'Failed to retrieval container list. Reason: ' + data.message,
                        'alert-danger');
                }
                setTimeout(function () {
                    // turnoff loading screens
                    containersTable.clear();
                    containersTable.rows.add(container_list);
                    containersTable.draw();
                    $("#containers-filter").prop("disabled", false);
                    $("#containers-table-loading").hide();
                    // turnoff loading screens
                    filesTable.clear().draw();
                    $("#files-filter").prop("disabled", false);
                    $("#files-table-loading").hide();
                }, 100);
            });
    }

    // loading container info when click to a container in table
    $('#containers-table').on('click', 'tbody tr', function () {
        // console.log($(this).data('container-name'));
        if (!$(this).data('container-name')) {
        }
        else if ($(this).hasClass('selected')) {
            // $(this).removeClass('selected');
            // $(this).find('td').html($(this).data('container-name').toString());
            // filesTable.clear().draw();
            // empty files table
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
                })
                .fail(function (jqXHR, textStatus, error) {
                    // Handle error here
                    alert_message(
                        'Failed to retrieval container list. Reason: ' + textStatus,
                        'alert-danger');
                })
                .always(function (data) {
                    let containerInfo = data.container_info;
                    let objectList = []
                    if (data.result === 'success') {
                        let containerSize = containerInfo.size;
                        let containerSizeDisplay;
                        let createdDateDisplay;
                        if (containerSize >= 512) {
                            containerSizeDisplay = containerSize / 1024 + ' GB';
                        } else {
                            containerSizeDisplay = containerSize + ' MB';
                        }
                        var monthNames = ["January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"
                        ];
                        // console.log(containerInfo);
                        let createdDate = new Date(containerInfo.date_created);
                        createdDateDisplay = monthNames[createdDate.getMonth()] + ' ' + createdDate.getDay() + ', ' + createdDate.getFullYear();
                        let containerInfoHtml = $('#container-info-soure').html();
                        let containerInfoBox = $('<td/>').html(containerInfoHtml);
                        containerInfoBox.find("#container-name").html(containerInfo.container_name);
                        containerInfoBox.find("#object-count").html(containerInfo.object_count);
                        containerInfoBox.find("#container-size").html(containerSizeDisplay);
                        containerInfoBox.find("#date-created").html(createdDateDisplay);
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
                        objectList = containerInfo.object_list;
                    } else if (data.result === 'failed') {
                        alert_message(
                            'Failed to retrieval container list. Reason: ' + data.message,
                            'alert-danger');
                    }
                    setTimeout(function () {
                        // push data for files table
                        filesTable.clear().draw();
                        filesTable.rows.add(objectList);
                        filesTable.draw();
                        // turnoff loading screens
                        $("#containers-filter").prop("disabled", false);
                        $("#containers-table-loading").hide();
                        $("#files-filter").prop("disabled", false);
                        $("#files-table-loading").hide();
                    }, 100);
                });
            ;

        }
    });

    $('#containers-table').on('click', 'tbody tr .collapse-container-btn', function () {
        let trSelectedElement = $(this).closest('tr');
        $(trSelectedElement).find('td').html($(trSelectedElement).data('container-name').toString());
        filesTable.clear().draw();
        setTimeout(function () {
            $(trSelectedElement).removeClass('selected');
        }, 200);
        // empty files table
    });

    // Event listener to the two range filtering inputs to redraw on input
    $('#containers-filter').keyup(function () {
        containersTable.draw();
    });
    loadContainersTable();


    $('#files-filter').keyup(function () {
        // alert_message('Create cluster ring failed. Server Error!', 'alert-success');
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
        let createContainerApi = $('#containers-table').data("create-container-api");
        // console.log(inputContainerName);
        $.ajax({
            method: "POST",
            data: {'container_name': inputContainerName},
            url: createContainerApi
        })
            .done(function (data) {
                if (data.result === 'success') {
                    // console.log(data);
                    $('#create-container-modal').modal('hide');
                    setTimeout(function () {
                        alert_message(inputContainerName + ' is created.', 'alert-success');
                        loadContainersTable();
                    }, 100);
                } else {
                    setTimeout(function () {
                        $('#create-container-modal').modal('hide');
                        alert_message(
                            'Failed to create container ' + inputContainerName +
                            '. Reason: ' + data.message,
                            'alert-danger');
                    }, 100);
                }
            })
            .fail(function (jqXHR, textStatus, error) {
                // Handle error here
                setTimeout(function () {
                    $('#create-container-modal').modal('hide');
                    alert_message(
                        'Failed to create container ' + inputContainerName + '.Reason: ' + textStatus,
                        'alert-danger'
                    );
                }, 100);
            });

    });

    $("#upload-file").on('click', function () {
        let selectedContainer = containersTable.$('tr.selected');
        if (selectedContainer.length != 1) {
            alert_message(
                'Select extract container which you want to put uploaded file in !',
                'alert-warning');
        } else {
            console.log(selectedContainer);
            let selectecdContainerName = $(selectedContainer).data('container-name');
            $('#upload-file-modal').find("span#input-container-name").attr('data-container-name', selectecdContainerName);
            $('#upload-file-modal').find("span#input-container-name").html(selectecdContainerName);
            $("input#input-object-file[type=file]").val('');
            $("input#input-file-name").val('');

            $('#upload-file-modal').modal({
                backdrop: 'static',
                keyboard: false
            });

            $("select#input-object-file-option").val("economy");
            $("#create-data-object-submit-btn").prop("disabled", true);

        }
    });
    $("input#input-object-file[type=file]").on('change', function () {
        if ($("input#input-file-name").val().length == 0) {
            $("input#input-file-name").val(this.files[0].name);
        }
        ;
        $("#create-data-object-submit-btn").prop("disabled", false);
    });
    $("input#input-file-name").on("change paste keyup", function () {
        let fileObjectName = $(this).val();
        if (fileObjectName.length > 0 && $('input#input-object-file[type=file]').get(0).files.length > 0 &&
            $("#create-data-object-submit-btn").prop("disabled") == true) {
            $("#create-data-object-submit-btn").prop("disabled", false);
        }
        if (fileObjectName.length === 0 || $('input#input-object-file[type=file]').get(0).files.length === 0) {
            $("#create-data-object-submit-btn").prop("disabled", true);
        }
    });
    $("#create-data-object-submit-btn").on('click', function () {
        let optionName = $("select#input-object-file-option").val();
        let fileName = $("input#input-file-name").val();
        let containerName = $("#upload-file-modal #input-container-name").data('container-name');
        var newObjectFileData = new FormData();
        newObjectFileData.append('file_data', $('input#input-object-file[type=file]')[0].files[0]);
        newObjectFileData.append('container_name', containerName);
        newObjectFileData.append('file_name', fileName);
        newObjectFileData.append('option_name', optionName);
        $("#file-uploading-loading .loading-info").html('Uploading New File...');
        $("#file-uploading-loading").show();
        // console.log(containerName);
        // console.log(optionName);
        // console.log(fileName);
        $.ajax({
            // Your server script to process the upload
            url: $("#files-table").data('upload-file-api'),
            type: 'POST',

            // Form data
            data: newObjectFileData,

            // Tell jQuery not to process data or worry about content-type
            // You *must* include these options!
            cache: false,
            contentType: false,
            processData: false,

            // Custom XMLHttpRequest
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    // For handling the progress of the upload
                    myXhr.upload.addEventListener('progress', function (e) {
                        // if (e.lengthComputable) {
                        //     $('progress').attr({
                        //         value: e.loaded,
                        //         max: e.total,
                        //     });
                        // }
                    }, false);
                }
                return myXhr;
            },
        });
    });


});

