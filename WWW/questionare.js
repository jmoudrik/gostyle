
var app = angular.module('myApp', []);

function QuestionareCtrl($scope, $http, $window, $location) {
    $scope.questionare = new StyleQuestionare();
    $scope.group_lists = [];
    
    $scope.current_grouplist = undefined;
    $scope.current_index = undefined;

    // the players that the user added
    $scope.max_id = 0;
    $scope.players = [];
    
    $scope.not_skipped_not_filled = [];
    
    $scope.next_btn_text = 'Click here to take it!';

    $scope.status = '';

    // Load the players from the webapp

    $http.jsonp('/questionare-w/get_players?callback=JSON_CALLBACK'
    ).success(function(data){
        $scope.group_lists = data ;
        last = $scope.group_lists[ $scope.group_lists.length - 1 ];
        if( last.name != 'Additional')
	    $scope.group_lists.push({'name':'Additional', 'list':[]});
	    
        $scope.players = $scope.get_all_players();
        $scope.max_id =_.max(_.map($scope.players, function (player) { return player['id']; }));
        
        $scope.status = '' ;
    }).error(function(data, status) {
        $scope.status = 'Request failed, status: ' + status;
      });
      
    $scope.next_group = function (){
	if( $scope.current_index == undefined ){
	    $scope.current_index = 0;
	} else{
	    $scope.current_index += 1;
	}
	// now the current index is next index
	
	$scope.next_btn_text = 'Next Part';
	if( $scope.current_index == $scope.group_lists.length - 2){
	    $scope.next_btn_text = 'To the Last Step!'
	}
	
	$scope.current_grouplist = $scope.group_lists[$scope.current_index]
	
	if( $scope.current_index == $scope.group_lists.length - 1){
	    $scope.current_index = -1;
	}
	location.hash = "#quest_start"
    
    }

    // information about the interviewee
    $scope.strength_list = str_list();
    $scope.intervi_str = '';
    $scope.intervi_feedback = '';

    var locname = ($location.search()).intervi_name;
    $scope.intervi_name = locname != undefined ? locname : '';

    var intervi_key = ($location.search()).intervi_key;
    $scope.intervi_key = intervi_key != undefined ? intervi_key : '';

    $scope.submit_error = ''
    $scope.new_name = '';

    // functions
    
    $scope.addNewPlayer = function(){
	var newp = $scope.questionare.make_new($scope.new_name, $scope.max_id + 1);
        $scope.current_grouplist.list.push(newp);
        $scope.players.push(newp);
        $scope.max_id += 1;
        $scope.update_skips();
        
        $scope.new_name = '';
    }
    
    $scope.get_all_players = function () {
	return _.flatten( _.map($scope.group_lists, function(group_list){return group_list['list'];}));
    }

    $scope.areAllStylesSelected = function(player){
        return _.all(_.values(player['style']), function (val){
            return val != '';
        });
    }
    
    $scope.update_skips = function(){
	if( $scope.current_grouplist == undefined ){
	    $scope.not_skipped_not_filled = [];
	
	}else{
	    var not_skipped = _.filter($scope.current_grouplist.list, function(player){
		return player['skip'] == 'no'; });
		
	    $scope.not_skipped_not_filled = _.reject(not_skipped, $scope.areAllStylesSelected);
        }
    }
    
    $scope.notAllPlayersFilled = function(){
	$scope.update_skips();
        return $scope.not_skipped_not_filled.length != 0;
    }
    

    $scope.submit = function(){
	var data = { 
	    'interviewee_name' : $scope.intervi_name
	    ,'interviewee_key' : $scope.intervi_key
	    ,'interviewee_str' : $scope.strength_list[$scope.intervi_str]
	    ,'interviewee_feedback' : $scope.intervi_feedback
	    ,'group_lists' : $scope.group_lists };
	// yep!
	$http({
	    method: 'POST',
	    url: '/questionare-w/submit',
	    data: angular.toJson(data),
	    headers:"a {'Content-Type': 'application/json'} "
	}).success(function(){
	    $window.location = '/questionare_thanks.html';
	}).error(function(){
	    $scope.submit_error = 'We are sorry, an error occured during submitting the Results. Please try again later.';
	});
    }
}

app.directive('nameUniq', function() {
  return {
    require: 'ngModel',
    link: function(scope, elm, attrs, ctrl) {
      ctrl.$parsers.push(function(viewValue) {
        var is_valid = ! _.contains(_.map(scope.players, function (player){return player['name'];}), viewValue);
        
        if (is_valid) {
          // it is valid
          ctrl.$setValidity('nameUniq', true);
          return viewValue;
        } else {
          // it is invalid, return undefined (no model update)
          ctrl.$setValidity('nameUniq', false);
          return undefined;
        }
      });
    }
  };
});

app.directive('nameNonempty', function() {
  return {
    require: 'ngModel',
    link: function(scope, elm, attrs, ctrl) {
      ctrl.$parsers.push(function(viewValue) {
        if (viewValue != '') {
          // it is valid
          ctrl.$setValidity('nameNonempty', true);
          return viewValue;
        } else {
          // it is invalid, return undefined (no model update)
          ctrl.$setValidity('nameNonempty', false);
          return undefined;
        }
      });
    }
  };
});

app.directive('strNonempty', function() {
  return {
    require: 'ngModel',
    link: function(scope, elm, attrs, ctrl) {
      ctrl.$parsers.push(function(viewValue) {
        if (viewValue != '') {
          // it is valid
          ctrl.$setValidity('strNonempty', true);
          return viewValue;
        } else {
          // it is invalid, return undefined (no model update)
          ctrl.$setValidity('strNonempty', false);
          return undefined;
        }
      });
    }
  };
});
