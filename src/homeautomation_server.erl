-module(homeautomation_server).

-behaviour(gen_server).

-export([start_link/0]).

-export([init/1, stop/0, handle_call/3, handle_cast/2, handle_info/2,
         terminate/2, code_change/3, start_timers/2]).

start_link() ->
    
    gen_server:start_link({local, ?MODULE}, ?MODULE, [], []).

init([]) ->
    txrx_server:log_terminal(off),
    txrx_server:log_file(on, "log/txrx.txt"),

    case application:get_env(homeautomation, device) of
	{ok, List} ->
	    
	    %% First we need to set the routing information
	    %% for all devices (i.e. Address & Unit)
	    update_device_info(List),
	    
	    check_devices_for_timers(List);
	_ ->
	    ok
    end,
    {ok, []}.

stop() ->
    txrx_server:tab2file(),
    init:stop().


update_device_info([]) ->
    ok;
update_device_info([Device|Devices]) ->
    {Id, Address, Unit, _Name, _List} = Device,
    txrx_server:set_device_info(Address, Unit, Id),    
    update_device_info(Devices).

check_devices_for_timers([]) ->
    ok;
check_devices_for_timers([Device|Devices]) ->
    {Id, _Address, _Unit, _Name, List} = Device,
    start_timers(Id, List),
    check_devices_for_timers(Devices).

start_timers(_Id, []) ->
    ok;

start_timers(Id, [{Cmd, Time}|Events]) ->    
    Msg = {Id, Cmd, Time, permanent},
    gen_server:cast(?MODULE, {start_timer, Msg}),
    start_timers(Id, Events).


date_diff(D1, D2) ->    
    calendar:datetime_to_gregorian_seconds(D1) -
        calendar:datetime_to_gregorian_seconds(D2).

next_day({Date, Time}) ->
    Days = calendar:date_to_gregorian_days(Date),
    NextDate = calendar:gregorian_days_to_date(Days+1),
    {NextDate, Time}.

%% callbacks

handle_call(_Request, _From, State) ->
    error_logger:info_msg("1 Timeout!~n", []),
    Reply = ok,
    {reply, Reply, State}.

handle_cast({start_timer, Msg}, State) -> 
        {_, _, EventTime, _} = Msg,
    Now = calendar:local_time(),
    {NowDate, _} = Now,
    TimeOut = {NowDate, EventTime},
    Diff = date_diff(TimeOut, Now),
    
    %% We use 1 instead of 0 to make sure we don't start new timer 
    %% for todays timeout
    Secs = if Diff > 1  -> Diff;
	      Diff =< 1 -> date_diff(next_day(TimeOut), Now)
	   end,
    
    timer:send_after(Secs*1000, self(), {timeout, Msg}),
    error_logger:info_msg("Starting timer with tmo value ~p secs~n", [Secs]),
    {noreply, State};

handle_cast(_Msg, State) ->
    error_logger:info_msg("2 Timeout!~n", []),
    {noreply, State}.

handle_info({timeout, Msg}, State) ->    
    error_logger:info_msg("Timeout Msg=~p Time=~p ~n", [Msg, calendar:local_time()]),
    {Id, Cmd, _Time, Type} = Msg,
    txrx_server:device(Id, Cmd),

    case Type of
	permanent ->
	    gen_server:cast(?MODULE, {start_timer, Msg});
	_Transient -> ok
    end,
    {noreply, State};

handle_info(_Info, State) ->
    error_logger:info_msg("3 Timeout!~n", []),
    {noreply, State}.

terminate(_Reason, _State) ->
    ok.

code_change(_OldVsn, State, _Extra) ->
    {ok, State}.
