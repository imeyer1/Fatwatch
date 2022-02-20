
$(document).ready(function ($)
{
    $(document).find('.btn_save').hide();
    $(document).find('.btn_cancel').hide();

})
//edit 	
$(document).on('click', '.btn_edit', function (event) 
{
    event.preventDefault();
    var tbl_row = $(this).closest('tr');
    var row_id = tbl_row.attr('row_id');

    tbl_row.find('.btn_save').show();
    tbl_row.find('.btn_cancel').show();

    //hide edit and delete button
    tbl_row.find('.btn_edit').hide();
    tbl_row.find('.btn_delete').hide();

    tbl_row.find('.row_data ').not(':first').not(':last').not(':last')
    .attr('contenteditable', 'true')
    .attr('edit_type', 'button')
    .addClass('bg-info')
    .css('padding','3px')
    //original entry if user cancel
    tbl_row.find('.row_data').each(function (index, val) 
    {
        $(this).attr('original_entry', $(this).html());
    });
});

//cancel	
$(document).on('click', '.btn_cancel', function (event) 
{
    var tbl_row = $(this).closest('tr');
    var row_id = tbl_row.attr('row_id');

    //hide save and cacel buttons
    tbl_row.find('.btn_save').hide();
    tbl_row.find('.btn_cancel').hide();

    //show edit and delete button
    tbl_row.find('.btn_edit').show();
    tbl_row.find('.btn_delete').show();

    var is_empty=$('td:first', $(this).parents('tr')).text().trim()
    if(is_empty != "")
    {
        tbl_row.find('.row_data').each(function (index, val) 
        {       
            $(this).html($(this).attr('original_entry'));
        });
        //make the whole row non-editable
        tbl_row.find('.row_data ').not(':first').not(':last').not(':last')
        .attr('edit_type', 'button')
        .removeClass('bg-info')
        .css('padding', '')
    }
    else
    {
        //make the whole row non-editable
        tbl_row.remove();
    }
});

//save 
$(document).on('click', '.btn_save', function (event) 
{
    // event.preventDefault();
    var title = document.getElementsByClassName("title")[0].innerHTML;
    var prefix = document.getElementsByClassName("prefix")[0].innerHTML;
    var tbl_row = $(this).closest('tr');
    var row_id = tbl_row.attr('row_id');
    //hide save and cacel buttons
    tbl_row.find('.btn_save').hide();
    tbl_row.find('.btn_cancel').hide();
    //show edit and delete button
    tbl_row.find('.btn_edit').show();
    tbl_row.find('.btn_delete').show();
    //make the whole row non-editable
    tbl_row.find('.row_data')
        .attr('edit_type', 'click')
        .removeClass('bg-info')
        .css('padding', '')
    //get row
    var arr = Array();
    tbl_row.find('.row_data').each(function (index, val) 
    {
        var col_name = $(this).attr('col_name');
        var col_val = $(this).html();
        arr[index] = col_val;
    });
    //use the "arr"	object for your ajax call
     $.extend(arr, { row_id: row_id });
     var is_empty=$('td:first', $(this).parents('tr')).text().trim()
    if(is_empty != "")
    {
    //show message
     $('.post_msg').html('<pre class="bg-info">"Record successfully Updated"</pre>')
     //output to change
    $.post("/update", {arr:arr, "title":title, "prefix":prefix}, function(data) {$("#displaymessage").html(data);
    $("#displaymessage").show();
    $('#table').html(function() {
            location.reload(true);
        });
    });
    }
    else
        {
            //show message
        $('.post_msg').html('<pre class="bg-info">"Record successfully added"</pre>')
        //output to change
        $.post("/add", {arr:arr, "title":title, "prefix":prefix}, function(data) {$("#displaymessage").html(data);
        $("#displaymessage").show();
        $('#table').html(function() {
            location.reload(true);
        });
        });
        }
        

});

//delete row
$(document).on('click',".btn_delete", function(event)
{
    var title = document.getElementsByClassName("title")[0].innerHTML;
    var prefix = document.getElementsByClassName("prefix")[0].innerHTML;
    var tbl_row = $(this).closest('tr');
    var id = $(this).closest('tr').children('td:first').text();
    
    tbl_row.remove();
    
    //show message
    $('.post_msg').html('<pre class="bg-info">"Record successfully deleted"</pre>')
     //output to delete
    $.post("/delete", {"title" : title, "id" :id, "prefix" :prefix}, function(data){  $("#displaymessage").html(data);
    $("#displaymessage").show();
    $('#table').html(function() {
            location.reload(true);
        });
    });
});
//add row
$(document).on('click',".btn_new", function(event)
{
    event.preventDefault();
    var tableBody = $('#table').find("tbody");
    rows = $('#table').find("tbody").length;
    console.log("rows: "+rows)
    //if data eexists
    if (rows > 1)
    {
        tr_last = tableBody.find("tr:last"),
        tr_new = tr_last.clone();
        tr_last.after(tr_new).val;
        tr_new.find('.row_data ').empty()
        tr_new.find('.row_data ').not(':first').not(':last')
            .attr('contenteditable', 'true')
            .attr('edit_type', 'button')
            .addClass('bg-info')
            .css('padding','3px')
        tr_new.find('.btn_save').show();
        tr_new.find('.btn_cancel').show();
        tr_new.find('td').first().focus();

        //hide edit and delete button
        tr_new.find('.btn_edit').hide();
        tr_new.find('.btn_delete').hide();
    }
    else{
        
        var colCount = $('#table th').length-2;
        $('#table').find('tbody');
        var tr_new = '<tr class="table-row" row_id="{{row[0]}} ">'
            $('#table').find('tbody').append(tr_new);
        console.log(tr_new)
        }
});



