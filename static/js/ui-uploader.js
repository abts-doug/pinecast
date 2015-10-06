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

            maxUploadSize: document.querySelector('main').getAttribute('data-max-upload-size') | 0,
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

    isImage: function() {
        if (this.state.finalContentURL && this.props.accept === 'image/*') return true;
        var fileObj = this.state.fileObj;
        return (fileObj ? fileObj.type || '' : '').split('/')[0] === 'image';
    },

    getImageURL: function() {
        var s = this.state.finalContentURL.split('.');
        s.pop();
        return s.join('.');
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
                this.props.optional ? null : React.createElement(
                    'input',
                    {
                        type: 'file',
                        required: 'required',
                        style: {display: 'none'},
                    }
                )
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
                        this.state.fileObj.size ? React.createElement('dt', null, gettext('Size:')) : null,
                        this.state.fileObj.size ? React.createElement('dd', null, this.state.fileObj.size) : null,
                        this.state.fileObj.name ? React.createElement('dt', null, gettext('Name:')) : null,
                        this.state.fileObj.name ? React.createElement('dd', null, this.getSafeName(this.state.fileObj.name)) : null,
                        this.state.fileObj.type ? React.createElement('dt', null, gettext('Type:')) : null,
                        this.state.fileObj.type ? React.createElement('dd', null, this.state.fileObj.type) : null
                    ) : null),
                this.renderPreview(),
                React.createElement(
                    'button',
                    {
                        className: 'btn-danger uploader-btn',
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
                        value: this.getSafeName(this.state.fileObj.name) || '',
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
                'data-text-drop': gettext('or drop a file to upload'),
            }),
            this.getError(),
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
                    required: this.props.optional ? null : 'required',
                }
            )
        );
    },

    renderPreview: function() {
        if (!this.isImage()) return null;

        return React.createElement(
            'div',
            {
                className: 'uploader-preview',
                style: {
                    backgroundImage: 'url(' + this.getImageURL() + ')',
                    backgroundPosition: 'center center',
                    backgroundSize: 'cover',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    height: '150px',
                    maxWidth: '350px',
                    width: '40%',
                }
            }
        );
    },

    setNewFile: function(fileObj) {
        if (fileObj.size > this.state.maxUploadSize) {
            this.setState({dragging: 0, error: 'file_too_big'});
            return;
        }
        if (this.props.type === 'image' && fileObj.size > 1024 * 1024 * 2) {
            this.setState({dragging: 0, error: 'image_too_big'});
            return;
        }
        this.setState({
            dragging: 0,
            fileObj: fileObj,
            uploading: true,
            error: null,
        });

        this.detectSize(fileObj);

        getFields(
            this.props.podcast,
            this.props.type,
            fileObj.type,
            this.getSafeName(fileObj.name),
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
        switch (fileObj.type) {
            case 'image/jpeg':
            case 'image/jpg':
            case 'image/png':
                return this.detectImageSize(fileObj);
            case 'audio/mp3':
            case 'audio/m4a':
            case 'audio/wav':
                return this.detectAudioSize(fileObj);
        }
    },

    detectImageSize: function(fileObj) {
        if (this.props.noiTunesSizeCheck) return;
        if (!window.FileReader) return;
        var fr = new FileReader();
        fr.onload = function() {
            if (this.state.fileObj !== fileObj) return;
            var i = new Image();
            i.src = fr.result;
            if (i.width < 1400 || i.height < 1400) {
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

    detectAudioSize: function(fileObj) {
        if (!this.props.audioDurationSelector) {
            return;
        }
        try {
            var blobURL = (window.URL || window.webkitURL || window.mozURL).createObjectURL(fileObj);
            var audio = new Audio(blobURL);
            audio.addEventListener('loadedmetadata', function() {
                var dur = audio.duration | 0;
                var durLab = document.querySelector(this.props.audioDurationSelector);
                var durHours = durLab.querySelector('[name="duration-hours"]');
                var durMinutes = durLab.querySelector('[name="duration-minutes"]');
                var durSeconds = durLab.querySelector('[name="duration-seconds"]');

                durHours.value = dur / 3600 | 0;
                durMinutes.value = dur % 3600 / 60 | 0;
                durSeconds.value = dur % 60 | 0;
            }.bind(this));
        } catch (e) {}
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
                    gettext('Warning! The image does not meet the iTunes minimum size of 1400x1400px.')
                );
            case 'not_square':
                return React.createElement(
                    'div',
                    {className: 'warning'},
                    gettext('Warning! The image is not square. This may cause distortion on some devices.')
                );
            case 'file_too_big':
                return React.createElement(
                    'div',
                    {className: 'warning'},
                    gettext('The file you are trying to upload is too large for your plan.')
                );
            case 'image_too_big':
                return React.createElement(
                    'div',
                    {className: 'warning'},
                    gettext('Images are limited to 2MB. Please select an image file with a smaller file size.')
                );
        }
        return null;
    },

    getSafeName: function(name) {
        return name.replace(/[^a-zA-Z0-9\._\-]/g, '_');
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
            audioDurationSelector: field.getAttribute('data-audio-duration-selector'),

            optional: field.getAttribute('data-optional') || false,
        }),
        field
    );
});

}());
