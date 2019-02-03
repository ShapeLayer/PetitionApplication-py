varHTML = document.getElementById('fetea-vars');
varTemplate = '<div class="row"><div class="col"><div class="form-group"><label for="{num}-key"></label><input type="text" class="form-control" name="{num}-key" id="{num}-key" value="" placeholder="키"></div></div><div class="col"><div class="form-group"><label for="{num}-var"></label><input type="text" class="form-control" name="{num}-var" id="{num}-var" value="" placeholder="값"></div></div></div>';

function add_var_list () {
    varHTML.innerHTML = varHTML.innerHTML + varTemplate.replace('{num}', varLen);
    varLen++;
}