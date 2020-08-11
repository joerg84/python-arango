from __future__ import absolute_import, unicode_literals

__all__ = ['Backup']

from arango.api import APIWrapper
from arango.exceptions import (
    BackupCreateError,
    BackupDeleteError,
    BackupDownloadError,
    BackupGetError,
    BackupRestoreError,
    BackupUploadError
)
from arango.formatter import (
    format_backup,
    format_backup_restore,
    format_backup_transfer
)
from arango.request import Request


class Backup(APIWrapper):

    def __init__(self, connection, executor):
        super(Backup, self).__init__(connection, executor)

    def get(self, backup_id=None):
        """Return backup details.

        :param backup_id: If set, details on only the specified backup is
            returned. Otherwise details on all backups are returned.
        :type backup_id: str
        :return: Backup details.
        :rtype: dict
        :raise arango.exceptions.BackupGetError: If delete fails.
        """
        request = Request(
            method='post',
            endpoint='/_admin/backup/list',
            data={} if backup_id is None else {'id': backup_id}
        )

        def response_handler(resp):
            if resp.is_success:
                backups = resp.body['result']['list']
                for key in backups:
                    backups[key] = format_backup(backups[key])
                return resp.body['result']
            raise BackupGetError(resp, request)

        return self._execute(request, response_handler)

    def create(self,
               label=None,
               allow_inconsistent=None,
               force=None,
               timeout=None):
        """Create a backup when the global write lock can be obtained.

        :param label: Backup label. If not given, a UUID is used.
        :type label: str
        :param allow_inconsistent: Allow inconsistent backup when the global
            transaction lock cannot be acquired before timeout. Default value
            is False.
        :type allow_inconsistent: bool
        :param force: Forcefully abort all running transactions to ensure a
            consistent backup when the global transaction lock cannot be
            acquired before timeout. Default (and highly recommended) value
            is False.
        :type force: bool
        :param timeout: Timeout in seconds for creating the backup. Default
            value is 120 seconds.
        :type timeout: int
        :return: Result of the create operation.
        :rtype: dict
        :raise arango.exceptions.BackupCreateError: If create fails.
        """
        data = {'label': label}

        if allow_inconsistent is not None:
            data['allowInconsistent'] = allow_inconsistent
        if force is not None:
            data['force'] = force
        if timeout is not None:
            data['timeout'] = timeout

        request = Request(
            method='post',
            endpoint='/_admin/backup/create',
            data=data
        )

        def response_handler(resp):
            if resp.is_success:
                return format_backup(resp.body['result'])
            raise BackupCreateError(resp, request)

        return self._execute(request, response_handler)

    def delete(self, backup_id):
        """Delete a backup.

        :param backup_id: Backup ID.
        :type backup_id: str
        :return: True if the backup was deleted successfully.
        :rtype: bool
        :raise arango.exceptions.BackupDeleteError: If delete fails.
        """
        request = Request(
            method='post',
            endpoint='/_admin/backup/delete',
            data={'id': backup_id}
        )

        def response_handler(resp):
            if resp.is_success:
                return True
            raise BackupDeleteError(resp, request)

        return self._execute(request, response_handler)

    def download(self,
                 backup_id=None,
                 repository=None,
                 abort=None,
                 config=None,
                 download_id=None):
        """Manage backup downloads.

        :param backup_id: Backup ID used for scheduling a download. Mutually
            exclusive with parameter **download_id**.
        :type backup_id: str
        :param repository: Remote repository URL (e.g. "local://tmp/backups").
            Required for scheduling a download and mutually exclusive with
            parameter **download_id**.
        :type repository: str
        :param config: Remote repository configuration. Required for scheduling
            a download and mutually exclusive with parameter **download_id**.
        :type config: dict
        :param download_id: Download ID. Mutually exclusive with parameters
            **backup_id**, **repository**, and **config**.
        :type download_id: str
        :param abort: If set to True, running download is aborted. Used with
            parameter **download_id**.
        :type abort: bool
        :return: Download details.
        :rtype: dict
        :raise arango.exceptions.BackupDownloadError: If operation fails.
        """
        data = {}
        if download_id is not None:
            data['downloadId'] = download_id
        if backup_id is not None:
            data['id'] = backup_id
        if repository is not None:
            data['remoteRepository'] = repository
        if abort is not None:
            data['abort'] = abort
        if config is not None:
            data['config'] = config

        request = Request(
            method='post',
            endpoint='/_admin/backup/download',
            data=data
        )

        def response_handler(resp):
            if resp.is_success:
                return format_backup_transfer(resp.body['result'])
            raise BackupDownloadError(resp, request)

        return self._execute(request, response_handler)

    def upload(self,
               backup_id=None,
               repository=None,
               abort=None,
               config=None,
               upload_id=None):
        """Manage backup uploads.

        :param backup_id: Backup ID used for scheduling an upload. Mutually
            exclusive with parameter **upload_id**.
        :type backup_id: str
        :param repository: Remote repository URL (e.g. "local://tmp/backups").
            Required for scheduling a upload and mutually exclusive with
            parameter **upload_id**.
        :type repository: str
        :param config: Remote repository configuration. Required for scheduling
            an upload and mutually exclusive with parameter **upload_id**.
        :type config: dict
        :param upload_id: Upload ID. Mutually exclusive with parameters
            **backup_id**, **repository**, and **config**.
        :type upload_id: str
        :param abort: If set to True, running upload is aborted. Used with
            parameter **upload_id**.
        :type abort: bool
        :return: Upload details.
        :rtype: dict
        :raise arango.exceptions.BackupUploadError: If upload operation fails.
        """
        data = {}

        if upload_id is not None:
            data['uploadId'] = upload_id
        if backup_id is not None:
            data['id'] = backup_id
        if repository is not None:
            data['remoteRepository'] = repository
        if abort is not None:
            data['abort'] = abort
        if config is not None:
            data['config'] = config

        request = Request(
            method='post',
            endpoint='/_admin/backup/upload',
            data=data
        )

        def response_handler(resp):
            if resp.is_success:
                return format_backup_transfer(resp.body['result'])
            raise BackupUploadError(resp, request)

        return self._execute(request, response_handler)

    def restore(self, backup_id):
        """Restore from a local backup.

        :param backup_id: Backup ID.
        :type backup_id: str
        :return: Result of the restore operation.
        :rtype: dict
        :raise arango.exceptions.BackupRestoreError: If restore fails.
        """
        request = Request(
            method='post',
            endpoint='/_admin/backup/restore',
            data={'id': backup_id}
        )

        def response_handler(resp):
            if resp.is_success:  # pragma: no cover
                return format_backup_restore(resp.body['result'])
            raise BackupRestoreError(resp, request)

        return self._execute(request, response_handler)
