/**
 * Created by cong on 20/11/2017.
 */

$(document).ready(function () {
    $('[rel="tooltip"]').tooltip({
        container: 'body',
        trigger: 'hover'
    });
    function handleFailedAjaxRequest(jqXHR, textStatus, error, msgHeader) {
        // console.log(jqXHR);
        if (jqXHR.status == 403) {
            alert_message(
                msgHeader + ' Reason: Token Expired! ' +
                'Redirecting to login page...',
                'alert-danger');

            setTimeout(function () {
                window.location.replace($("#login-url").data('login-url'));
            }, 1000);

        } else {
            alert_message(
                msgHeader + 'Reason: ' + jqXHR.responseJSON.message,
                'alert-danger');
        }
    }

    let containersTable = $('#containers-table').DataTable(
        {
            'createdRow': function (row, data, dataIndex) {
                // console.log(data.name);
                $(row).attr('data-container-name', data.info);
            },
            scrollY: '400px',
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
                    "width": "5%",
                    "data": null,
                    "defaultContent": ''
                },
                {
                    "className": "btn-center",
                    "width": "25%", "targets": -1,
                    "orderable": false,
                    "data": function (row, type, val, meta) {
                        // load downloadlink for each object
                        // console.log(row);
                        // console.log(val);
                        let downloadUrl = $('#files-table').data('file-download-api');
                        downloadUrl += '?account_name=' + row.account_name;
                        downloadUrl += '&container_name=' + row.container_name;
                        downloadUrl += '&file_name=' + row.object_name;
                        let fileActions = $("#file-actions-source").html();
                        let fileActionsBox = $(fileActions);
                        // console.log(fileActionsBox.find('a.btn-download-file')[0]);
                        // console.log(downloadUrl);
                        $(fileActionsBox.find('a.btn-download-file')[0]).attr('href', downloadUrl);
                        fileActionsBox.attr('data-object-name', row.file_name);
                        // console.log(fileActionsBox.prop('outerHTML'));
                        // return "<button>Edit</button>";
                        return fileActionsBox.prop('outerHTML');
                    }
                },
                {
                    "data": "object_name",
                    "render": function (data, type, row) {
                        if (data.length >= 25) {
                            data = data.substring(0, 22) + '...';
                        }
                        return data;
                    },
                    "targets": 1,
                    "width": "30%",
                },
                {
                    "width": "25%",
                    "data": "last_update", "targets": 2,
                    "render": function (data, type, row) {
                        let lastUpdate = moment.utc(data, "YYYY-MM-DD HH:mm:ss.SS");
                        // createdDateDisplay = moment(lastUpdate).local().format('YYYY MMM DD');
                        // console.log(data);
                        return moment(lastUpdate).local().format('DD-MM-YYYY HH:mm:ss');
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
                {
                    "data": "size", "targets": 3,
                    "width": "15%",
                    "render": function (data, type, row) {
                        if (data < 512) {
                            return data + " byte"
                        }
                        else if (512 <= data && data <= 1024 * 1024 * 0.5) {
                            return (data * 1.0 / 1024).toFixed(2) + " KB"
                        }
                        else if (1024 * 1024 * 0.5 <= data && data < 1024 * 1024 * 512) {
                            return (data * 1.0 / (1024 * 1024)).toFixed(2) + " MB"
                        }
                        else if (1024 * 1024 * 512 <= data && data < 1024 * 1024 * 1024 * 512) {
                            return (data * 1.0 / (1024 * 1024 * 1024)).toFixed(2) + " GB"
                        }

                    }

                },
            ],
            'createdRow': function (row, data, dataIndex) {
                // console.log(data.name);
                $(row).attr('data-file-name', data.object_name);
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
            fixedColumns: true,
            'autoWidth': false,
            "pageLength": 9
            // "pageLength": 9
        }
    );

    // show object info
    $('#files-table').on('click', 'tbody tr .btn-info-file', function () {
        let trSelectedElement = $(this).closest('tr');
        let selectedFileName = $(trSelectedElement).data('file-name').toString();
        let selectedContainerName = containersTable.$('tr.selected').data('container-name').toString();
        $('#file-info-modal').modal();
        $("#file-info-loading .loading-info").html('Loading File Info...');
        $("#file-info-loading").show();
        $.ajax({
            method: "GET",
            data: {
                'file_name': selectedFileName,
                'container_name': selectedContainerName
            },
            url: $('#files-table').data('file-info-api')
        })
            .done(function (data) {
                // console.log(data);
                if (data.result == 'success') {
                    let objectInfo = data.object_info;
                    let fileInfoDisplay = $('#file-info-modal').find('#file-info');
                    $(fileInfoDisplay).empty();
                    for (var key in objectInfo) {
                        if (key == 'last_update') {
                            let lastUpdate = moment.utc(objectInfo[key], "YYYY-MM-DD HH:mm:ss.SS");
                            // createdDateDisplay = moment(lastUpdate).local().format('YYYY MMM DD');
                            // console.log(data);
                            lastUpdate = moment(lastUpdate).local().format('DD-MM-YYYY HH:mm:ss');
                            fileInfoDisplay.append($('<dt>' + key + '</dt>'));
                            fileInfoDisplay.append($('<dd>' + lastUpdate + '</dd>'));
                        } else if (key == 'file_size') {
                            let fileSize = '';
                            let data = parseInt(objectInfo[key]);
                            if (data < 512) {
                                fileSize = data + " byte"
                            }
                            else if (512 <= data && data <= 1024 * 1024 * 0.5) {
                                fileSize = (data * 1.0 / 1024).toFixed(2) + " KB"
                            }
                            else if (1024 * 1024 * 0.5 <= data && data < 1024 * 1024 * 512) {
                                fileSize = (data * 1.0 / (1024 * 1024)).toFixed(2) + " MB"
                            }
                            else if (1024 * 1024 * 512 <= data && data < 1024 * 1024 * 1024 * 512) {
                                fileSize = (data * 1.0 / (1024 * 1024 * 1024)).toFixed(2) + " GB"
                            }
                            fileInfoDisplay.append($('<dt>' + key + '</dt>'));
                            fileInfoDisplay.append($('<dd>' + fileSize + '</dd>'));

                        } else {
                            fileInfoDisplay.append($('<dt>' + key + '</dt>'));
                            fileInfoDisplay.append($('<dd>' + objectInfo[key] + '</dd>'));
                        }
                        // console.log(key, yourobject[key]);
                    }

                } else {
                    alert_message(
                        'Failed to load file info.' + 'Reason: ' + data.message,
                        'alert-danger');
                }
            })
            .fail(function (jqXHR, textStatus, error) {
                handleFailedAjaxRequest(jqXHR, textStatus, error, 'Failed to load file info.');
            })
            .always(function (data) {
                $("#file-info-loading").hide();
            });
    });


    // update file data
    // show object info
    $('#files-table').on('click', 'tbody tr .btn-update-file', function () {
        let trSelectedElement = $(this).closest('tr');
        let selectedFileName = $(trSelectedElement).data('file-name').toString();
        let selectedContainerName = containersTable.$('tr.selected').data('container-name').toString();
        $("#update-file-modal").find("#update-absolute-file")
            .html(selectedContainerName + '.' + selectedFileName);
        $("#update-file-modal").find("#update-container-name")
            .val(selectedContainerName);
        $("#update-file-modal").find("#update-file-name")
            .val(selectedFileName);
        $('#update-file-modal').modal();
        // $("#file-info-loading .loading-info").html('Loading File Info...');
        // $("#file-info-loading").show();
    });


    $('#files-table').on('click', 'tbody tr .btn-delete-file', function () {
        let trSelectedElement = $(this).closest('tr');
        let selectedFileName = $(trSelectedElement).data('file-name').toString();
        let selectedContainerName = containersTable.$('tr.selected').data('container-name').toString();
        $("#delete-file-modal").find("#container-name")
            .val(selectedContainerName);
        $("#delete-file-modal").find("#delete-file-name")
            .val(selectedFileName);
        $("#delete-file-modal").find("#file-name")
            .html(selectedFileName);
        $('#delete-file-modal').modal();
    });

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
                handleFailedAjaxRequest(jqXHR, textStatus, error, 'Failed to load container list.');
            })
            .always(function (data) {
                // console.log(data);
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

    function loadContainerDetails(selectedContainerRow) {
        let isRowSelected = false;
        if ($(selectedContainerRow).hasClass('selected')) {
            isRowSelected = true;
        }
        // console.log(isRowSelected);
        // let selectedContainerRow = $('#containers-table').find('tr.selected');
        // show loading screens in containers table and files table
        $("#containers-filter").prop("disabled", true);
        $("#containers-table-loading .loading-info").html('Loading Container Information...');
        $("#containers-table-loading").show();

        $("#files-filter").prop("disabled", true);
        $("#files-table-loading .loading-info").html('Loading File Object List...');
        $("#files-table-loading").show();

        let selectedRow = $(selectedContainerRow);
        let tblElement = $('#containers-table');
        let getContainerInfoApi = tblElement.data("container-info-api");
        $.ajax({
            method: "GET",
            data: {'container_name': $(selectedContainerRow).data('container-name').toString()},
            url: getContainerInfoApi
        })
            .done(function (data) {
            })
            .fail(function (jqXHR, textStatus, error) {
                handleFailedAjaxRequest(jqXHR, textStatus, error, 'Failed to load container details.');
            })
            .always(function (data) {
                let containerInfo = data.container_info;
                let objectList = []
                if (data.result === 'success') {
                    let containerSize = containerInfo.size.toFixed(2);
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
                    // var date = moment.utc("22017-11-29 21:57:03.258749", "YYYY-MM-DD HH:mm:ss.SS")
                    // console.log(moment(date).local().format('YYYY-MMM-DD h:mm A'));
                    // console.log(containerInfo.date_created);
                    let createdDate = moment.utc(containerInfo.date_created, "YYYY-MM-DD HH:mm:ss.SS");
                    createdDateDisplay = moment(createdDate).local().format('YYYY MMM DD');
                    let containerInfoHtml = $('#container-info-soure').html();
                    let selectedRowTd = $(selectedRow).find('td');
                    $(selectedRowTd).html(containerInfoHtml);
                    selectedRowTd.find("#container-name").html(containerInfo.container_name);
                    selectedRowTd.find("#object-count").html(containerInfo.object_count);
                    selectedRowTd.find("#container-size").html(containerSizeDisplay);
                    selectedRowTd.find("#date-created").html(createdDateDisplay);
                    if (!isRowSelected) {
                        let prevSelectedRow = containersTable.$('tr.selected');
                        if (prevSelectedRow.length !== 0) {
                            // console.log(selectedRow);
                            prevSelectedRow.find('td')
                                .html($(prevSelectedRow).data('container-name').toString());
                            prevSelectedRow.removeClass('selected');
                        }
                        $(selectedRow).addClass('selected');

                    }
                    objectList = containerInfo.object_list;
                    // console.log(objectList);
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
                    // load downloadlink for each object
                    // console.log($("#files-table").find('a.btn-download-file'));
                    // $("#files-table").find('a.btn-download-file').each(function () {
                    //     console.log(this);
                    // })
                    // turnoff loading screens
                    $("#containers-filter").prop("disabled", false);
                    $("#containers-table-loading").hide();
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
            // $(this).addClass('selected');
            loadContainerDetails(this);
        }
    });


    // delete container
    $('#containers-table').on('click', 'tbody tr .delete-container-btn', function () {
        let trContainerRow = $(this).closest('tr');
        let containerName = $(trContainerRow).data('container-name');
        let objectCount = parseInt(trContainerRow.find("#object-count").html());
        if (objectCount > 0) {
            alert_message(
                'Failed to delete container ' + containerName +
                '. Reason: container is not empty!',
                'alert-danger');
        } else {
            $("#delete-container-modal").find('#deleted-container-name').html(containerName);
            $("#delete-container-modal").modal();
        }
    });

    $('#containers-table').on('click', 'tbody tr .collapse-container-btn', function () {
        // console.log('deleted!');
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
        $("#create-container-loading .loading-info").html('Creating new container...');
        $("#create-container-loading").show();
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
                    handleFailedAjaxRequest(jqXHR, textStatus, error,
                        'Failed to create container ' + inputContainerName);
                }, 100);
            })
            .always(function (data) {
                $("#create-container-loading").hide();
                $('#create-container-modal').modal('hide');
            });

    });

    $("#upload-file").on('click', function () {
        let selectedContainerRow = containersTable.$('tr.selected');
        console.log(selectedContainerRow.data('container-name'));
        if (selectedContainerRow.length != 1) {
            alert_message(
                'Select extract container which you want to put uploaded file in !',
                'alert-warning');
        } else {
            // console.log(selectedContainerRow);
            let selectecdContainerName = $(selectedContainerRow).data('container-name');
            $('#upload-file-modal').find("span#input-container-name").attr('data-container-name', selectecdContainerName);
            $('#upload-file-modal').find("#upload-container-name").val(selectecdContainerName);
            $('#upload-file-modal').find("input#input-object-file[type=file]").val('');
            $('#upload-file-modal').find("input#input-file-name").val('');

            $('#upload-file-modal').modal({
                backdrop: 'static',
                keyboard: false
            });

            $("select#input-object-file-option").val("optimize");
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
        let containerName = $("#upload-file-modal").find("#upload-container-name").val();
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
        })
            .done(function (data) {
                if (data.result === 'success') {
                    loadContainerDetails
                    // console.log(data);
                    setTimeout(function () {
                        alert_message('New file ' + fileName + ' is uploaded.', 'alert-success');
                        let selectedContainerRow = containersTable.$('tr.selected');
                        // console.log(selectedContainerRow);
                        // console.log(!selectedContainerRow.hasClass('selected'));
                        loadContainerDetails(selectedContainerRow);
                    }, 100);
                } else {
                    setTimeout(function () {
                        alert_message(
                            'Failed to create object ' + fileName +
                            '. Reason: ' + data.message,
                            'alert-danger');
                    }, 100);
                }
            })
            .fail(function (jqXHR, textStatus, error) {
                handleFailedAjaxRequest(jqXHR, textStatus, error, 'Failed to create object ' + fileName);
            })
            .always(function (data) {
                $("#file-uploading-loading").hide();
                $('#upload-file-modal').modal('hide');
            });
        ;
    });


    $("#delete-container-submit-btn").on('click', function () {
        let containerName = $('#delete-container-modal').find('#deleted-container-name').html();
        let deleteContainerApi = $('#containers-table').data("delete-container-api");
        $("#delete-container-loading .loading-info").html('Deleting container...');
        $("#delete-container-loading").show();
        $.ajax({
            method: "POST",
            data: {'container_name': containerName},
            url: deleteContainerApi
        })
            .done(function (data) {
                if (data.result === 'success') {
                    $('#delete-container-modal').modal('hide');
                    setTimeout(function () {
                        alert_message(containerName + ' is deleted.', 'alert-success');
                        loadContainersTable();
                    }, 100);
                } else {
                    setTimeout(function () {
                        $('#delete-container-modal').modal('hide');
                        alert_message(
                            'Failed to delete container ' + containerName +
                            '. Reason: ' + data.message,
                            'alert-danger');
                    }, 100);
                }
            })
            .fail(function (jqXHR, textStatus, error) {
                // Handle error here
                setTimeout(function () {
                    handleFailedAjaxRequest(jqXHR, textStatus, error,
                        'Failed to create container ' + containerName);
                }, 100);
            })
            .always(function (data) {
                $("#delete-container-loading").hide();
                $('#delete-container-modal').modal('hide');
            });
    });

    $('#update-file-modal').on('hidden.bs.modal', function () {
        let updateFileForm = $("#update-file-modal")
        $(updateFileForm).find('#update-object-data').val("");
    })

    // handle update file submit button
    $("#update-data-object-submit-btn").on('click', function () {
        let updateFileForm = $("#update-file-modal")
        let fileName = $(updateFileForm).find("#update-file-name").val();
        let containerName = $(updateFileForm).find("#update-container-name").val();
        let updateData = $(updateFileForm).find('#update-object-data')[0].files[0];
        console.log(fileName);
        console.log(containerName);
        console.log(updateData);
        if (updateData != null) {
            var newObjectFileData = new FormData();
            newObjectFileData.append('file_data', updateData);
            newObjectFileData.append('container_name', containerName);
            newObjectFileData.append('file_name', fileName);
            $("#file-update-loading .loading-info").html('Update File Data...');
            $("#file-update-loading").show();
            $.ajax({
                url: $("#files-table").data('update-file-api'),
                type: 'POST',
                data: newObjectFileData,
                cache: false,
                contentType: false,
                processData: false,
                xhr: function () {
                    var myXhr = $.ajaxSettings.xhr();
                    if (myXhr.upload) {
                        myXhr.upload.addEventListener('progress', function (e) {
                        }, false);
                    }
                    return myXhr;
                },
            })
                .done(function (data) {
                    if (data.result === 'success') {
                        setTimeout(function () {
                            alert_message('File ' + fileName + ' is updated data.', 'alert-success');
                            let selectedContainerRow = containersTable.$('tr.selected');
                            loadContainerDetails(selectedContainerRow);
                        }, 100);
                    } else {
                        setTimeout(function () {
                            alert_message(
                                'Failed to update data for file ' + fileName +
                                '. Reason: ' + data.message,
                                'alert-danger');
                        }, 100);
                    }
                })
                .fail(function (jqXHR, textStatus, error) {
                    handleFailedAjaxRequest(jqXHR, textStatus, error, 'Failed to update data for file ' + fileName);
                })
                .always(function (data) {
                    $("#file-update-loading").hide();
                    $('#update-file-modal').modal('hide');
                });
        }
    });


    // handle update file submit button
    $("#delete-data-object-submit-btn").on('click', function () {
        let deleteFileForm = $("#delete-file-modal")
        let fileName = $(deleteFileForm).find("#delete-file-name").val();
        let containerName = $(deleteFileForm).find("#container-name").val();
        $("#delete-file-loading .loading-info").html('Deleting File...');
        $("#delete-file-loading").show();
        $.ajax({
            url: $("#files-table").data('delete-file-api'),
            type: 'POST',
            data: {
                'container_name': containerName,
                'object_name': fileName
            },
        })
            .done(function (data) {
                if (data.result === 'success') {
                    setTimeout(function () {
                        alert_message('File ' + fileName + ' is deleted.', 'alert-success');
                        let selectedContainerRow = containersTable.$('tr.selected');
                        loadContainerDetails(selectedContainerRow);
                    }, 100);
                } else {
                    setTimeout(function () {
                        alert_message(
                            'Failed to delete file ' + fileName +
                            '. Reason: ' + data.message,
                            'alert-danger');
                    }, 100);
                }
            })
            .fail(function (jqXHR, textStatus, error) {
                handleFailedAjaxRequest(jqXHR, textStatus, error, 'Failed to delete file ' + fileName);
            })
            .always(function (data) {
                $("#delete-file-loading").hide();
                $('#delete-file-modal').modal('hide');
            });
    });

    // end document ready
});
