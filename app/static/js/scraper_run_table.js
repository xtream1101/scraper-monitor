'use strict';

_.templateSettings = {interpolate: /\{\{(.+?)\}\}/g};

var ScraperRunTable = function(){
    this.templates = {
        scraperWrapper: _.template(
            '<table id={{runClass}}-{{scraperKey}} class="table">' +
                '<thead class="invisible">' +
                    '<tr>' +
                        '<th class="scraper-name">Name</th>' +
                        '<th>Start Time</th>' +
                        '<th>Stop Time</th>' +
                        '<th>Runtime</th>' +
                        '<th>Log Criticals</th>' +
                        '<th>Log Errors</th>' +
                        '<th>Log Warnings</th>' +
                        '<th>URL Errors</th>' +
                    '</tr>' +
                '</thead>' +
                '<tbody class="panel-heading" data-toggle="collapse" href="#collapse-{{runClass}}-{{scraperKey}}">' +
                    '<tr id="{{uuid}}">' +
                        '<td class="scraper-name">{{name}}</td>' +
                        '<td>{{startTime}}</td>' +
                        '<td>{{stopTime}}</td>' +
                        '<td>{{runtime}}</td>' +
                        '<td>{{criticalCount}}</td>' +
                        '<td>{{errorCount}}</td>' +
                        '<td>{{warningCount}}</td>' +
                        '<td>{{urlErrorCount}}</td>' +
                    '</tr>' +
                '</tbody>' +
                '<tbody id="collapse-{{runClass}}-{{scraperKey}}" class="collapse runs">' +
                '</tbody>' +
            '</table>'
        ),
        scraperRun: _.template(
            '<tr id="{{uuid}}">' +
                '<td class="scraper-name"></td>' +
                '<td>{{startTime}}</td>' +
                '<td>{{stopTime}}</td>' +
                '<td>{{runtime}}</td>' +
                '<td>{{criticalCount}}</td>' +
                '<td>{{errorCount}}</td>' +
                '<td>{{warningCount}}</td>' +
                '<td>{{urlErrorCount}}</td>' +
            '</tr>'
        ),
    }
};

ScraperRunTable.prototype.somethingBS = function(){

};
