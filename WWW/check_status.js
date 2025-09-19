
String.prototype.repeat = function(count) {
    if (count < 1) return '';
    var result = '', pattern = this.valueOf();
    while (count > 0) {
        if (count & 1) result += pattern;
        count >>= 1, pattern += pattern;
    }
    return result;
};

var app = angular.module('webApp', []);

function CheckCtrl($scope, $location, $timeout, $http) {
    $scope.id = ($location.search()).id;
    $scope.check_count = 0;
    $scope.pending_for = 0;
    
    $scope.state = 'Not checked yet';
    $scope.state_style = {};
    $scope.result = '';
    
    $scope.on_timeout = function(){
        $http.jsonp('/webapp-w/get_status?callback=JSON_CALLBACK&id='+$scope.id
        ).success(function(data){
        
            var state = data['state'];
            var result = data['result'];
            
            if( state == 'REDIRECT' ){
                $scope.id = result;
                state = 'WORKING';
                result = 'Archives extracted.'
            }
            
            $scope.state = state;
            $scope.result = result;
            $scope.check_result();
        }).error(function(data, status) {
            $scope.state = 'FAILURE';
            $scope.result = status;
            $scope.check_result();
          });
          
        $scope.check_count += 1;
        mytimeout = $timeout($scope.on_timeout, 2000);
    }
    
    $scope.stop_timeout = function(){
        $timeout.cancel(mytimeout);
    }
    
    $scope.check_result = function(){
        if( $scope.state == 'FAILURE' ){
            $scope.stop_timeout();
            $scope.state_class = 'text-danger';
            $scope.check_count = 0;
        }
        
        if( $scope.state == 'PENDING' ){
            $scope.pending_for += 1;
        }else{
            $scope.pending_for = 0;
        }
        
        if( $scope.state == 'SUCCESS' ){
        
            $scope.stop_timeout();
            $scope.state_class = 'text-success';
            $scope.check_count = 0;
            window.location = $scope.result;
        }
    }
    $scope.on_timeout();
}
