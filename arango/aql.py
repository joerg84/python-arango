from __future__ import absolute_import, unicode_literals

__all__ = ['AQL', 'AQLQueryCache']

from arango.api import APIWrapper
from arango.cursor import Cursor
from arango.exceptions import (
    AQLQueryExplainError,
    AQLQueryValidateError,
    AQLQueryExecuteError,
    AQLQueryListError,
    AQLQueryClearError,
    AQLQueryTrackingGetError,
    AQLQueryKillError,
    AQLQueryTrackingSetError,
    AQLFunctionCreateError,
    AQLFunctionDeleteError,
    AQLFunctionListError,
    AQLCacheEntriesError,
    AQLCacheClearError,
    AQLCacheConfigureError,
    AQLCachePropertiesError
)
from arango.formatter import (
    format_aql_cache,
    format_aql_query,
    format_aql_tracking
)
from arango.request import Request


class AQL(APIWrapper):
    """AQL (ArangoDB Query Language) API wrapper.

    :param connection: HTTP connection.
    :type connection: arango.connection.Connection
    :param executor: API executor.
    :type executor: arango.executor.Executor
    """

    def __init__(self, connection, executor):
        super(AQL, self).__init__(connection, executor)

    def __repr__(self):
        return '<AQL in {}>'.format(self._conn.db_name)

    @property
    def cache(self):
        """Return the query cache API wrapper.

        :return: Query cache API wrapper.
        :rtype: arango.aql.AQLQueryCache
        """
        return AQLQueryCache(self._conn, self._executor)

    def explain(self, query, all_plans=False, max_plans=None, opt_rules=None):
        """Inspect the query and return its metadata without executing it.

        :param query: Query to inspect.
        :type query: str
        :param all_plans: If set to True, all possible execution plans are
            returned in the result. If set to False, only the optimal plan
            is returned.
        :type all_plans: bool
        :param max_plans: Total number of plans generated by the optimizer.
        :type max_plans: int
        :param opt_rules: List of optimizer rules.
        :type opt_rules: list
        :return: Execution plan, or plans if **all_plans** was set to True.
        :rtype: dict | list
        :raise arango.exceptions.AQLQueryExplainError: If explain fails.
        """
        options = {'allPlans': all_plans}
        if max_plans is not None:
            options['maxNumberOfPlans'] = max_plans
        if opt_rules is not None:
            options['optimizer'] = {'rules': opt_rules}

        request = Request(
            method='post',
            endpoint='/_api/explain',
            data={'query': query, 'options': options}
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryExplainError(resp, request)
            if 'plan' in resp.body:
                return resp.body['plan']
            else:
                return resp.body['plans']

        return self._execute(request, response_handler)

    def validate(self, query):
        """Parse and validate the query without executing it.

        :param query: Query to validate.
        :type query: str
        :return: Query details.
        :rtype: dict
        :raise arango.exceptions.AQLQueryValidateError: If validation fails.
        """
        request = Request(
            method='post',
            endpoint='/_api/query',
            data={'query': query}
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryValidateError(resp, request)
            body = resp.body
            body.pop('code', None)
            body.pop('error', None)
            if 'bindVars' in body:
                body['bind_vars'] = body.pop('bindVars')
            return body

        return self._execute(request, response_handler)

    def execute(self,
                query,
                count=False,
                batch_size=None,
                ttl=None,
                bind_vars=None,
                full_count=None,
                max_plans=None,
                optimizer_rules=None,
                cache=None,
                memory_limit=0,
                fail_on_warning=None,
                profile=None,
                max_transaction_size=None,
                max_warning_count=None,
                intermediate_commit_count=None,
                intermediate_commit_size=None,
                satellite_sync_wait=None,
                read_collections=None,
                write_collections=None,
                stream=None,
                skip_inaccessible_cols=None,
                max_runtime=None):
        """Execute the query and return the result cursor.

        :param query: Query to execute.
        :type query: str
        :param count: If set to True, the total document count is included in
            the result cursor.
        :type count: bool
        :param batch_size: Number of documents fetched by the cursor in one
            round trip.
        :type batch_size: int
        :param ttl: Server side time-to-live for the cursor in seconds.
        :type ttl: int
        :param bind_vars: Bind variables for the query.
        :type bind_vars: dict
        :param full_count: This parameter applies only to queries with LIMIT
            clauses. If set to True, the number of matched documents before
            the last LIMIT clause executed is included in the cursor. This is
            similar to MySQL SQL_CALC_FOUND_ROWS hint. Using this disables a
            few LIMIT optimizations and may lead to a longer query execution.
        :type full_count: bool
        :param max_plans: Max number of plans the optimizer generates.
        :type max_plans: int
        :param optimizer_rules: List of optimizer rules.
        :type optimizer_rules: [str]
        :param cache: If set to True, the query cache is used. The operation
            mode of the query cache must be set to "on" or "demand".
        :type cache: bool
        :param memory_limit: Max amount of memory the query is allowed to use
            in bytes. If the query goes over the limit, it fails with error
            "resource limit exceeded". Value 0 indicates no limit.
        :type memory_limit: int
        :param fail_on_warning: If set to True, the query throws an exception
            instead of producing a warning. This parameter can be used during
            development to catch issues early. If set to False, warnings are
            returned with the query result. There is a server configuration
            option "--query.fail-on-warning" for setting the default value for
            this behaviour so it does not need to be set per-query.
        :type fail_on_warning: bool
        :param profile: Return additional profiling details in the cursor,
            unless the query cache is used.
        :type profile: bool
        :param max_transaction_size: Transaction size limit in bytes.
        :type max_transaction_size: int
        :param max_warning_count: Max number of warnings returned.
        :type max_warning_count: int
        :param intermediate_commit_count: Max number of operations after
            which an intermediate commit is performed automatically.
        :type intermediate_commit_count: int
        :param intermediate_commit_size: Max size of operations in bytes after
            which an intermediate commit is performed automatically.
        :type intermediate_commit_size: int
        :param satellite_sync_wait: Number of seconds in which the server must
            synchronize the satellite collections involved in the query. When
            the threshold is reached, the query is stopped. Available only for
            enterprise version of ArangoDB.
        :type satellite_sync_wait: int | float
        :param read_collections: Names of collections read during query
            execution. This parameter is deprecated.
        :type read_collections: [str]
        :param write_collections: Names of collections written to during query
            execution. This parameter is deprecated.
        :type write_collections: [str]
        :param stream: If set to True, query is executed in streaming fashion:
            query result is not stored server-side but calculated on the fly.
            Note: long-running queries hold collection locks for as long as the
            cursor exists. If set to False, query is executed right away in its
            entirety. Results are either returned right away (if the result set
            is small enough), or stored server-side and accessible via cursors
            (while respecting the ttl). You should use this parameter only for
            short-running queries or without exclusive locks. Note: parameters
            **cache**, **count** and **full_count** do not work for streaming
            queries. Query statistics, warnings and profiling data are made
            available only after the query is finished. Default value is False.
        :type stream: bool
        :param skip_inaccessible_cols: If set to True, collections without user
            access are skipped, and query executes normally instead of raising
            an error. This helps certain use cases: a graph may contain several
            collections, and users with different access levels may execute the
            same query. This parameter lets you limit the result set by user
            access. Cannot be used in :doc:`transactions <transaction>` and is
            available only for enterprise version of ArangoDB. Default value is
            False.
        :type skip_inaccessible_cols: bool
        :param max_runtime: Query must be executed within this given timeout or
            it is killed. The value is specified in seconds. Default value
            is 0.0 (no timeout).
        :type max_runtime: int | float
        :return: Result cursor.
        :rtype: arango.cursor.Cursor
        :raise arango.exceptions.AQLQueryExecuteError: If execute fails.
        """
        data = {'query': query, 'count': count}
        if batch_size is not None:
            data['batchSize'] = batch_size
        if ttl is not None:
            data['ttl'] = ttl
        if bind_vars is not None:
            data['bindVars'] = bind_vars
        if cache is not None:
            data['cache'] = cache
        if memory_limit is not None:
            data['memoryLimit'] = memory_limit

        options = {}
        if full_count is not None:
            options['fullCount'] = full_count
        if max_plans is not None:
            options['maxNumberOfPlans'] = max_plans
        if optimizer_rules is not None:
            options['optimizer'] = {'rules': optimizer_rules}
        if fail_on_warning is not None:
            options['failOnWarning'] = fail_on_warning
        if profile is not None:
            options['profile'] = profile
        if max_transaction_size is not None:
            options['maxTransactionSize'] = max_transaction_size
        if max_warning_count is not None:
            options['maxWarningCount'] = max_warning_count
        if intermediate_commit_count is not None:
            options['intermediateCommitCount'] = intermediate_commit_count
        if intermediate_commit_size is not None:
            options['intermediateCommitSize'] = intermediate_commit_size
        if satellite_sync_wait is not None:
            options['satelliteSyncWait'] = satellite_sync_wait
        if stream is not None:
            options['stream'] = stream
        if skip_inaccessible_cols is not None:
            options['skipInaccessibleCollections'] = skip_inaccessible_cols
        if max_runtime is not None:
            options['maxRuntime'] = max_runtime

        if options:
            data['options'] = options
        data.update(options)

        request = Request(
            method='post',
            endpoint='/_api/cursor',
            data=data,
            read=read_collections,
            write=write_collections
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryExecuteError(resp, request)
            return Cursor(self._conn, resp.body)

        return self._execute(request, response_handler)

    def kill(self, query_id):
        """Kill a running query.

        :param query_id: Query ID.
        :type query_id: str
        :return: True if kill request was sent successfully.
        :rtype: bool
        :raise arango.exceptions.AQLQueryKillError: If the send fails.
        """
        request = Request(
            method='delete',
            endpoint='/_api/query/{}'.format(query_id)
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryKillError(resp, request)
            return True

        return self._execute(request, response_handler)

    def queries(self):
        """Return the currently running AQL queries.

        :return: Running AQL queries.
        :rtype: [dict]
        :raise arango.exceptions.AQLQueryListError: If retrieval fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/query/current'
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryListError(resp, request)
            return [format_aql_query(q) for q in resp.body]

        return self._execute(request, response_handler)

    def slow_queries(self):
        """Return a list of all slow AQL queries.

        :return: Slow AQL queries.
        :rtype: [dict]
        :raise arango.exceptions.AQLQueryListError: If retrieval fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/query/slow'
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryListError(resp, request)
            return [format_aql_query(q) for q in resp.body]

        return self._execute(request, response_handler)

    def clear_slow_queries(self):
        """Clear slow AQL queries.

        :return: True if slow queries were cleared successfully.
        :rtype: bool
        :raise arango.exceptions.AQLQueryClearError: If operation fails.
        """
        request = Request(
            method='delete',
            endpoint='/_api/query/slow'
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryClearError(resp, request)
            return True

        return self._execute(request, response_handler)

    def tracking(self):
        """Return AQL query tracking properties.

        :return: AQL query tracking properties.
        :rtype: dict
        :raise arango.exceptions.AQLQueryTrackingGetError: If retrieval fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/query/properties'
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryTrackingGetError(resp, request)
            return format_aql_tracking(resp.body)

        return self._execute(request, response_handler)

    def set_tracking(self,
                     enabled=None,
                     max_slow_queries=None,
                     slow_query_threshold=None,
                     max_query_string_length=None,
                     track_bind_vars=None,
                     track_slow_queries=None):
        """Configure AQL query tracking properties

        :return: Updated AQL query tracking properties.
        :rtype: dict
        :raise arango.exceptions.AQLQueryTrackingSetError: If operation fails.
        """
        data = {}
        if enabled is not None:
            data['enabled'] = enabled
        if max_slow_queries is not None:
            data['maxSlowQueries'] = max_slow_queries
        if max_query_string_length is not None:
            data['maxQueryStringLength'] = max_query_string_length
        if slow_query_threshold is not None:
            data['slowQueryThreshold'] = slow_query_threshold
        if track_bind_vars is not None:
            data['trackBindVars'] = track_bind_vars
        if track_slow_queries is not None:
            data['trackSlowQueries'] = track_slow_queries

        request = Request(
            method='put',
            endpoint='/_api/query/properties',
            data=data
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLQueryTrackingSetError(resp, request)
            return format_aql_tracking(resp.body)

        return self._execute(request, response_handler)

    def functions(self):
        """List the AQL functions defined in the database.

        :return: AQL functions.
        :rtype: [dict]
        :raise arango.exceptions.AQLFunctionListError: If retrieval fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/aqlfunction'
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLFunctionListError(resp, request)

            body = resp.body or {}

            if 'result' not in body:  # pragma: no cover
                return []

            for item in body['result']:
                if 'isDeterministic' in item:
                    item['is_deterministic'] = item.pop('isDeterministic')

            return body['result']

        return self._execute(request, response_handler)

    def create_function(self, name, code):
        """Create a new AQL function.

        :param name: AQL function name.
        :type name: str
        :param code: Function definition in Javascript.
        :type code: str
        :return: Whether the AQL function was newly created or an existing one
            was replaced.
        :rtype: dict
        :raise arango.exceptions.AQLFunctionCreateError: If create fails.
        """
        request = Request(
            method='post',
            endpoint='/_api/aqlfunction',
            data={'name': name, 'code': code}
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLFunctionCreateError(resp, request)
            return {'is_new': resp.body['isNewlyCreated']}

        return self._execute(request, response_handler)

    def delete_function(self, name, group=False, ignore_missing=False):
        """Delete an AQL function.

        :param name: AQL function name.
        :type name: str
        :param group: If set to True, value of parameter **name** is treated
            as a namespace prefix, and all functions in the namespace are
            deleted. If set to False, the value of **name** must be a fully
            qualified function name including any namespaces.
        :type group: bool
        :param ignore_missing: Do not raise an exception on missing function.
        :type ignore_missing: bool
        :return: Number of AQL functions deleted if operation was successful,
            False if function(s) was not found and **ignore_missing** was set
            to True.
        :rtype: dict | bool
        :raise arango.exceptions.AQLFunctionDeleteError: If delete fails.
        """
        request = Request(
            method='delete',
            endpoint='/_api/aqlfunction/{}'.format(name),
            params={'group': group}
        )

        def response_handler(resp):
            if resp.error_code == 1582 and ignore_missing:
                return False
            if not resp.is_success:
                raise AQLFunctionDeleteError(resp, request)
            return {'deleted': resp.body['deletedCount']}

        return self._execute(request, response_handler)


class AQLQueryCache(APIWrapper):
    """AQL Query Cache API wrapper."""

    def __repr__(self):
        return '<AQLQueryCache in {}>'.format(self._conn.db_name)

    def properties(self):
        """Return the query cache properties.

        :return: Query cache properties.
        :rtype: dict
        :raise arango.exceptions.AQLCachePropertiesError: If retrieval fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/query-cache/properties'
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLCachePropertiesError(resp, request)
            return format_aql_cache(resp.body)

        return self._execute(request, response_handler)

    def configure(self,
                  mode=None,
                  max_results=None,
                  max_results_size=None,
                  max_entry_size=None,
                  include_system=None):
        """Configure the query cache properties.

        :param mode: Operation mode. Allowed values are "off", "on" and
            "demand".
        :type mode: str
        :param max_results: Max number of query results stored per
            database-specific cache.
        :type max_results: int
        :param max_results_size: Max cumulative size of query results stored
            per database-specific cache.
        :type max_results_size: int
        :param max_entry_size: Max entry size of each query result stored per
            database-specific cache.
        :type max_entry_size: int
        :param include_system: Store results of queries in system collections.
        :type include_system: bool
        :return: Query cache properties.
        :rtype: dict
        :raise arango.exceptions.AQLCacheConfigureError: If operation fails.
        """
        data = {}
        if mode is not None:
            data['mode'] = mode
        if max_results is not None:
            data['maxResults'] = max_results
        if max_results_size is not None:
            data['maxResultsSize'] = max_results_size
        if max_entry_size is not None:
            data['maxEntrySize'] = max_entry_size
        if include_system is not None:
            data['includeSystem'] = include_system

        request = Request(
            method='put',
            endpoint='/_api/query-cache/properties',
            data=data
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLCacheConfigureError(resp, request)
            return format_aql_cache(resp.body)

        return self._execute(request, response_handler)

    def entries(self):
        """Return the query cache entries.

        :return: Query cache entries.
        :rtype: list
        :raise AQLCacheEntriesError: If retrieval fails.
        """
        request = Request(
            method='get',
            endpoint='/_api/query-cache/entries'
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLCacheEntriesError(resp, request)
            return resp.body

        return self._execute(request, response_handler)

    def clear(self):
        """Clear the query cache.

        :return: True if query cache was cleared successfully.
        :rtype: bool
        :raise arango.exceptions.AQLCacheClearError: If operation fails.
        """
        request = Request(
            method='delete',
            endpoint='/_api/query-cache'
        )

        def response_handler(resp):
            if not resp.is_success:
                raise AQLCacheClearError(resp, request)
            return True

        return self._execute(request, response_handler)
