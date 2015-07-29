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
        var hasDef = !!this.props.defURL;
        return {
            uploading: false,
            uploaded: hasDef,
            progress: 0,
            fileObj: !hasDef ? null : {
                name: this.props.defName,
                size: this.props.defSize,
                type: this.props.defType,
            },
            error: null,
            dragging: 0,

            finalContentURL: hasDef ? this.props.defURL : null,
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
            return [
                React.createElement(
                    'div',
                    {className: 'progress'},
                    React.createElement('i', {style: {width: this.state.progress + '%'}})
                ),
                this.getError(),
            ];
        }

        if (this.state.uploaded) {
            return React.createElement(
                'div',
                {
                    className: 'uploaded-file-card'
                },
                React.createElement('b', null, gettext('File Uploaded')),
                (this.state.fileObj.size || this.state.fileObj.name || this.state.fileObj.type ?
                    React.createElement(
                        'dl',
                        null,
                        React.createElement('dt', null, gettext('Size:')),
                        React.createElement('dd', null, this.state.fileObj.size || gettext('Unknown')),
                        React.createElement('dt', null, gettext('Name:')),
                        React.createElement('dd', null, this.state.fileObj.name || gettext('Unknown')),
                        React.createElement('dt', null, gettext('Type:')),
                        React.createElement('dd', null, this.state.fileObj.type || gettext('Unknown'))
                    ) : null),
                React.createElement(
                    'button',
                    {
                        className: 'btn-warn',
                        onClick: this.clearFile,
                    },
                    gettext('Clear File')
                ),
                this.getError(),
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
                        name: this.props.name + '-name',
                        value: this.state.fileObj.name || '',
                    }
                ),
                React.createElement(
                    'input',
                    {
                        type: 'hidden',
                        name: this.props.name + '-size',
                        value: this.state.fileObj.size || '',
                    }
                ),
                React.createElement(
                    'input',
                    {
                        type: 'hidden',
                        name: this.props.name + '-type',
                        value: this.state.fileObj.type || '',
                    }
                )
            );
        }

        return React.createElement(
            'label',
            {
                className: 'upload-dd-label' + (this.state.dragging ? ' is-dragging' : ''),
                onDragEnter: function(e) {
                    // e.preventDefault();
                    this.setState({
                        dragging: this.state.dragging + 1,
                    });
                }.bind(this),
                onDragOver: function(e) {
                    e.preventDefault();
                }.bind(this),
                onDragLeave: function() {
                    this.setState({
                        dragging: this.state.dragging - 1,
                    });
                }.bind(this),
                onDrop: function(e) {
                    e.preventDefault();
                    this.setNewFile(e.dataTransfer.files[0]);
                }.bind(this),
            },
            React.createElement('i', {
                'data-text-choose': gettext('Choose a file to upload'),
                'data-text-drop': gettext('or Drop files to upload'),
            }),
            React.createElement(
                'input',
                {
                    type: 'file',
                    accept: this.props.accept,
                    onChange: function(e) {
                        var fileObj = this.refs.filePicker.getDOMNode().files[0];
                        this.setNewFile(fileObj);
                    }.bind(this),
                    ref: 'filePicker',
                    required: 'required',
                }
            )
        );
    },

    setNewFile: function(fileObj) {
        this.setState({
            dragging: 0,
            fileObj: fileObj,
            uploading: true,
        });

        this.detectSize(fileObj);

        getFields(
            this.props.podcast,
            this.props.type,
            fileObj.type,
            fileObj.name,
            function(err, data) {
                if (err) {
                    console.error(err);
                    alert(gettext('There was a problem contacting the server for upload information'));
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

    detectSize: function(fileObj) {
        if (this.props.noiTunesSizeCheck) return;
        if (!window.FileReader) return;
        switch (fileObj.type) {
            case 'image/jpeg':
            case 'image/jpg':
            case 'image/png':
                break;
            default:
                return;
        }

        var fr = new FileReader();
        fr.onload = function() {
            if (this.state.fileObj !== fileObj) return;
            var i = new Image();
            i.src = fr.result;
            if (i.width < 1440 || i.height < 1440) {
                this.setState({
                    error: 'min_size',
                });
            } else if (i.width !== i.height) {
                this.setState({
                    error: 'not_square',
                });
            }
        }.bind(this);
        fr.readAsDataURL(fileObj);
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
            alert(gettext('There was a problem while uploading the file'));
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

        xhr.open(fields.method, fields.url, true);
        for (key in fields.headers) {
            if (!fields.headers.hasOwnProperty(key)) continue;
            xhr.setRequestHeader(key, fields.headers[key]);
        }

        var data = new FormData();
        for (key in fields.fields) {
            if (!fields.fields.hasOwnProperty(key)) continue;
            data.append(key, fields.fields[key]);
        }
        data.append('file', this.state.fileObj);
        xhr.send(data);
    },

    clearFile: function(e) {
        e.preventDefault();
        this.setState({
            fileObj: null,
            finalContentURL: '',
            uploaded: false,
        });
    },

    getError: function() {
        if (!this.state.error) return;
        switch (this.state.error) {
            case 'min_size':
                return React.createElement(
                    'div',
                    {className: 'warning'},
                    gettext('Warning! The image does not meet the iTunes minimum size of 1440x1440px.')
                );
            case 'not_square':
                return React.createElement(
                    'div',
                    {className: 'warning'},
                    gettext('Warning! The image is not square. This may cause distortion on some devices.')
                );
        }
        return null;
    },

});


var fields = document.querySelectorAll('.upload-placeholder');
Array.prototype.slice.call(fields).forEach(function(field) {
    React.render(
        React.createElement(Uploader, {
            accept: field.getAttribute('data-accept'),
            name: field.getAttribute('data-name'),
            podcast: field.getAttribute('data-podcast'),
            type: field.getAttribute('data-type'),

            defURL: field.getAttribute('data-default-url'),
            defName: field.getAttribute('data-default-name'),
            defSize: field.getAttribute('data-default-size'),
            defType: field.getAttribute('data-default-type'),
            noiTunesSizeCheck: field.getAttribute('data-no-itunes-size-check') == 'true',
        }),
        field
    );
});

}());
