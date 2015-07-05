(function() {

function getFields(podcastSlug, type, fileType, fileName, cb) {
    var xhr = new XMLHttpRequest();
    xhr.onload = function() {
        cb(null, JSON.parse(xhr.responseText));
    };
    xhr.onerror = function() {
        cb(xhr.status);
    };
    xhr.open(
        'get',
        '/dashboard/services/getUploadURL/' + encodeURIComponent(podcastSlug) + '/' + encodeURIComponent(type) +
            '?type=' + encodeURIComponent(fileType) + '&name=' + encodeURIComponent(fileName),
        true
    );
    xhr.send();
}

var Uploader = React.createClass({

    getInitialState: function() {
        return {
            uploading: false,
            uploaded: false,
            progress: 0,
            fileObj: null,

            finalContentURL: null,
        };
    },

    render: function() {
        return React.createElement(
            'div',
            {
                className: 'uploader' + (this.state.uploading ? ' is-uploading' : '') + (this.state.uploaded ? ' is-uploaded' : ''),
            },
            this.getBody()
        );
    },

    getBody: function() {
        if (this.state.uploading) {
            return React.createElement(
                'div',
                {className: 'progress'},
                React.createElement('i', {style: {width: this.state.progress + '%'}})
            );
        }

        if (this.state.uploaded) {
            return React.createElement(
                'div',
                {
                    className: 'uploaded-file-card'
                },
                React.createElement('b', null, 'File Uploaded'),
                React.createElement(
                    'dl',
                    null,
                    React.createElement('dt', null, 'Size:'),
                    React.createElement('dd', null, this.state.fileObj.size),
                    React.createElement('dt', null, 'Name:'),
                    React.createElement('dd', null, this.state.fileObj.name),
                    React.createElement('dt', null, 'Type:'),
                    React.createElement('dd', null, this.state.fileObj.type)
                ),
                React.createElement(
                    'button',
                    {
                        className: 'btn-warn',
                        onClick: this.clearFile,
                    },
                    'Clear File'
                ),
                React.createElement(
                    'input',
                    {
                        type: 'hidden',
                        name: this.props.name,
                        value: this.state.finalContentURL,
                    }
                ),
                React.createElement(
                    'input',
                    {
                        type: 'hidden',
                        name: this.props.name + '-size',
                        value: this.state.fileObj.size,
                    }
                ),
                React.createElement(
                    'input',
                    {
                        type: 'hidden',
                        name: this.props.name + '-type',
                        value: this.state.fileObj.type,
                    }
                )
            );
        }

        return React.createElement(
            'input',
            {
                type: 'file',
                accept: this.props.accept,
                onChange: this.gotNewFile,
                ref: 'filePicker',
                required: 'required',
            }
        );
    },

    gotNewFile: function(event) {
        var fileObj = this.refs.filePicker.getDOMNode().files[0];
        this.setState({
            fileObj: fileObj,
            uploading: true,
        });

        getFields(
            this.props.podcast,
            this.props.type,
            fileObj.type,
            fileObj.name,
            function(err, data) {
                if (err) {
                    console.error(err);
                    alert('There was a problem contacting the server for upload information');
                    this.setState({
                        fileObj: null,
                        uploading: false,
                    });
                    return;
                }
                this.startUploading(data);
            }.bind(this)
        );
    },

    startUploading: function(fields) {
        var xhr = new XMLHttpRequest();

        xhr.onload = xhr.upload.onload = function() {
            this.setState({
                uploading: false,
                uploaded: true,
                finalContentURL: fields.destination_url,
            });
        }.bind(this);
        xhr.onerror = xhr.upload.onerror = function() {
            console.error(xhr);
            alert('There was a problem while uploading the file');
            this.setState({
                fileObj: null,
                uploading: false,
                progress: 0,
            });
        }.bind(this);
        xhr.upload.onprogress = function(e) {
            if (!e.lengthComputable) return;
            this.setState({
                progress: (e.loaded / e.total) * 100,
            });
        }.bind(this);

        xhr.open('put', fields.url, true);
        for (key in fields.headers) {
            if (!fields.headers.hasOwnProperty(key)) continue;
            xhr.setRequestHeader(key, fields.headers[key]);
        }
        xhr.send(this.state.fileObj);
    },

    clearFile: function(e) {
        e.preventDefault();
        this.setState({
            fileObj: null,
            finalContentURL: '',
            uploaded: false,
        });
    }

});


var fields = document.querySelectorAll('.upload-placeholder');
Array.prototype.slice.call(fields).forEach(function(field) {
    React.render(
        React.createElement(Uploader, {
            accept: field.getAttribute('data-accept'),
            name: field.getAttribute('data-name'),
            podcast: field.getAttribute('data-podcast'),
            type: field.getAttribute('data-type'),
        }),
        field
    );
});

}());
