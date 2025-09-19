function StyleQuestionare(){
	var keys = [ 'te', 'or', 'ag', 'th' ];

    this.keys = keys;
	this.long_names = {
		'te' : 'Territoriality', 
		// Orthodoxity -> Novelty changed on 27.5.2013
		'or' : 'Novelty',
		'ag' : 'Aggresivity',
		'th' : 'Thickness' }

	this.left = {
		'te' : 'Moyo', 
		'or' : 'Classic',
		'ag' : 'Calm',
		'th' : 'Safe' }

	this.right = {
		'te' : 'Territory', 
		'or' : 'Novel',
		'ag' : 'Fighting',
		'th' : 'Shinogi' }

	this.bound_left = {
		'te' : 1 ,
		'or' : 1,
		'ag' : 1,
		'th' : 1}

	this.bound_right = {
		'te' : 10,
		'or' : 10,
		'ag' : 10,
		'th' : 10}
	
	this.make_new = function(name, id, def_skip){
        def_skip = typeof def_skip !== 'undefined' ? def_skip : 'no' ;
		var new_item = { 'name' : name,
                         'id'  : id,
					 	 'style' : {},
						 'tags' : '',
						 'skip' : def_skip // "no" or "yes"
						 };

		for ( var key in this.keys ) {
            var keyit = this.keys[key];
			new_item['style'][keyit] = '';
                //(this.bound_right[keyit] + this.bound_left[keyit]) / 2;
		}
		return new_item;
	}

    this.bound_range = {};
    for ( var key in keys )
        this.bound_range[keys[key]] = _.range(this.bound_left[keys[key]],
                                              this.bound_right[keys[key]]+1);
}

function str_list(){
    return [
{"value" : "25", "text" : "25k or above"},
{"value" : "20", "text" : "20k - 25k"},
{"value" : "19", "text" : "19k"},
{"value" : "18", "text" : "18k"},
{"value" : "17", "text" : "17k"},
{"value" : "16", "text" : "16k"},
{"value" : "15", "text" : "15k"},
{"value" : "14", "text" : "14k"},
{"value" : "13", "text" : "13k"},
{"value" : "12", "text" : "12k"},
{"value" : "11", "text" : "11k"},
{"value" : "10", "text" : "10k"},
{"value" : "9", "text" : "9k"},
{"value" : "8", "text" : "8k"},
{"value" : "7", "text" : "7k"},
{"value" : "6", "text" : "6k"},
{"value" : "5", "text" : "5k"},
{"value" : "4", "text" : "4k"},
{"value" : "3", "text" : "3k"},
{"value" : "2", "text" : "2k"},
{"value" : "1", "text" : "1k"},
{"value" : "0", "text" : "1d"},
{"value" : "-1", "text" : "2d"},
{"value" : "-2", "text" : "3d"},
{"value" : "-3", "text" : "4d"},
{"value" : "-4", "text" : "5d"},
{"value" : "-5", "text" : "6d"},
{"value" : "-6", "text" : "7d"},
{"value" : "-7", "text" : "8d"},
{"value" : "-10", "text" : "1p"},
{"value" : "-11", "text" : "2p"},
{"value" : "-12", "text" : "3p"},
{"value" : "-13", "text" : "4p"},
{"value" : "-14", "text" : "5p"},
{"value" : "-15", "text" : "6p"},
{"value" : "-16", "text" : "7p"},
{"value" : "-17", "text" : "8p"},
{"value" : "-18", "text" : "9p"},
];
}

function str_list_kgs(){
    return [
{"value" : "25", "text" : "25k or above"},
{"value" : "20", "text" : "20k - 25k"},
{"value" : "19", "text" : "19k"},
{"value" : "18", "text" : "18k"},
{"value" : "17", "text" : "17k"},
{"value" : "16", "text" : "16k"},
{"value" : "15", "text" : "15k"},
{"value" : "14", "text" : "14k"},
{"value" : "13", "text" : "13k"},
{"value" : "12", "text" : "12k"},
{"value" : "11", "text" : "11k"},
{"value" : "10", "text" : "10k"},
{"value" : "9", "text" : "9k"},
{"value" : "8", "text" : "8k"},
{"value" : "7", "text" : "7k"},
{"value" : "6", "text" : "6k"},
{"value" : "5", "text" : "5k"},
{"value" : "4", "text" : "4k"},
{"value" : "3", "text" : "3k"},
{"value" : "2", "text" : "2k"},
{"value" : "1", "text" : "1k"},
{"value" : "0", "text" : "1d"},
{"value" : "-1", "text" : "2d"},
{"value" : "-2", "text" : "3d"},
{"value" : "-3", "text" : "4d"},
{"value" : "-4", "text" : "5d"},
{"value" : "-5", "text" : "6d"},
{"value" : "-6", "text" : "7d or above"},
];
}
