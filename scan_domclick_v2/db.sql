DROP TABLE if exists card_shotlar_v2 cascade;
CREATE TABLE card_shotlar_v2 (
	id serial4 NOT NULL,
	scan_session int8 NOT NULL,
	created_at timestamptz NOT NULL default now(),
	updated_at timestamptz NULL,
	external_id int8 NOT NULL,
	external_url TEXT NOT NULL,
	card jsonb NOT NULL,
	CONSTRAINT card_shotlar_v2_external_id_scan_session_key UNIQUE (external_id, scan_session),
	CONSTRAINT card_shotlar_v2_pkey PRIMARY KEY (id)
);


drop table if exists regionlar_v2;
CREATE TABLE regionlar_v2 (
	id smallserial NOT NULL,
	value text NOT NULL,
	aids int2 NOT NULL,
	code text NOT NULL,
	"name" text NOT NULL,
	for_news bool NULL,
	ord int2 NOT NULL,
	CONSTRAINT regionlar_v2_code_key UNIQUE (code),
	CONSTRAINT regionlar_v2_name_key UNIQUE (name),
	CONSTRAINT regionlar_v2_ord_key UNIQUE (ord),
	CONSTRAINT regionlar_v2_pkey PRIMARY KEY (id),
	CONSTRAINT regionlar_v2_value_key UNIQUE (value)
);

INSERT INTO regionlar_v2 (value,aids,code,"name",for_news,ord) VALUES
	 ('1d1463ae-c80f-4d19-9331-a1b68a85b553','2299','msk','Москва',NULL,1),
	 ('9930cc20-32c6-4f6f-a55e-cd67086c5171','2298','mo','Московская область',NULL,2);


drop table if exists facetlar_v2;
CREATE TABLE facetlar_v2 (
	id smallserial NOT NULL,
	deal_type TEXT NOT NULL,
	category TEXT NOT NULL,
	offer_type TEXT,
	"name" TEXT NOT NULL,
	ord int2 NOT NULL,
	CONSTRAINT facetlar_v2_value_key UNIQUE (deal_type, category, offer_type),
	CONSTRAINT facetlar_v2_pkey PRIMARY KEY (id)
);

INSERT INTO facetlar_v2 (deal_type,category,offer_type,"name",ord) VALUES
	 ('sale','living','flat','Квартира::Купить',1),
	 ('sale','living','layout','Новостройка::Купить',2),
	 ('rent','living','flat','Квартира::Снять',3),
	 ('sale','living','room','Комната::Купить',4),
	 ('rent','living','room','Комната::Снять',5),
	 ('sale','living','house','Дом,Дача::Купить',6),
	 ('rent','living','house','Дом,Дача::Снять',7),
	 ('sale','living','house_part','Часть дома::Купить',8),
	 ('rent','living','house_part','Часть дома::Снять',9),
	 ('sale','living','townhouse','Таунхаус::Купить',10),
	 ('rent','living','townhouse','Таунхаус::Снять',11),
	 ('sale','living','lot','Участок::Купить',12),
	 ('sale','commercial','comm','Коммерческая::Купить',13),
	 ('rent','commercial','comm','Коммерческая::Снять',14),
	 ('sale','garage','garage','Гаражи::Купить',15),
	 ('rent','garage','garage','Гаражи::Снять',16);



-- --------------------------------------


drop table if exists scan_sessionlar_v2 cascade;
create table scan_sessionlar_v2(
	id serial8 primary key,
	started_at timestamptz not null,
	finished_at timestamptz,
	region smallint not null references regionlar_v2(id) on delete cascade,
	facet smallint not null references facetlar_v2(id) on delete cascade,
	min_price int8 not null,
	page_num smallint not null
);


-- --------------------------------------


drop function if exists get_or_create_scan_session_v2(text, text, text);
create function get_or_create_scan_session_v2(
	_region_code text,
	_deal_type text,
	_offer_type text,
	out _session int,
	out _min_price int8, 
    out _page_num smallint
) 
as $$
declare 
	_region_id smallint;
	_facet_id smallint;
begin
	-- Получаем ID региона
	select id into _region_id
	from regionlar_v2
	where code = _region_code;
	
	-- Получаем ID фасета
	select id into _facet_id
	from facetlar_v2
	where deal_type = _deal_type 
		and offer_type = _offer_type;
	
	-- Ищем существующую незавершенную сессию
	select 
		id, min_price, page_num
		into _session, _min_price, _page_num
	from scan_sessionlar_v2
	where 
		region = _region_id 
		and facet = _facet_id 
		and finished_at is null
	order by id desc
	limit 1;

	-- Если сессия не найдена, создаем новую
	if _session is null then
		insert into scan_sessionlar_v2 (started_at, region, facet, min_price, page_num)
		values (NOW(), _region_id, _facet_id, 0, 1)
		returning id, min_price, page_num into _session, _min_price, _page_num;
	end if;
end;
$$ language plpgsql;


DROP FUNCTION if exists get_params_for_url_v2(text, text, text);
create function get_params_for_url_v2(
	p_region_code text,
	p_deal_type text,
	p_offer_type text,
	out o_region text,
	out o_aids text,
	out o_deal_type text,
	out o_category text,
	out o_offer_type text
) 
as $$
declare
	_facet_offer_type text;
begin
	select value, aids into o_region, o_aids
	from regionlar_v2
	where code = p_region_code;
	
	select 
		deal_type, category, offer_type
		into o_deal_type, o_category, _facet_offer_type
	from facetlar_v2
	where deal_type = p_deal_type 
		and offer_type = p_offer_type;

	if _facet_offer_type IN ('comm', 'garage') then
		o_offer_type := '';
	else
		o_offer_type := _facet_offer_type;
	end if;
end;
$$ language plpgsql;



DROP FUNCTION add_card_shot_v2(in int8, in int8, in text, in jsonb, out int4);
create function add_card_shot_v2(
	_scan_session bigint, 
	_external_id int8, 
	_external_url TEXT, 
	_card jsonb, 
	OUT _ret integer
	) 
as $$
declare 
begin
	select 
		into _ret id 
	from card_shotlar_v2
	where 
		external_id = _external_id and
		true;

	if _ret is null then
		insert into card_shotlar_v2 (scan_session, external_id, external_url, card)
		values (_scan_session, _external_id, _external_url, _card)
		returning id into _ret;
	else
		update card_shotlar_v2 
		set scan_session = _scan_session, card = _card, updated_at = now()
		where id = _ret;
	end if;
end;
$$ language plpgsql;


DROP FUNCTION if exists update_scan_session_v2(int8, smallint, int8);
create function update_scan_session_v2(
	_session_id int8,
	_page_num smallint,
	_min_price int8
) 
returns boolean
as $$
declare
	_updated_id int8;
begin
	update scan_sessionlar_v2
	set 
		page_num = _page_num,
		min_price = _min_price
	where id = _session_id
	returning id into _updated_id;
	
	return _updated_id is not null;
end;
$$ language plpgsql;


DROP FUNCTION if exists finish_scan_session_v2(int8);
create function finish_scan_session_v2(
	_session_id int8
) 
returns boolean
as $$
declare
	_updated_id int8;
begin
	update scan_sessionlar_v2
	set finished_at = NOW()
	where id = _session_id
	returning id into _updated_id;
	
	return _updated_id is not null;
end;
$$ language plpgsql;



DROP FUNCTION if exists get_params_for_dip_facet_v2(text, text, text);
create function get_params_for_dip_facet_v2(
	p_region_code text,
	p_deal_type text,
	p_offer_type text,
	out o_facet_name text
) 
as $$
declare
	_region_name text;
	_facet_name_part text;
begin
	-- получаем название региона
	select "name" into _region_name
	from regionlar_v2
	where code = p_region_code;
	
	-- получаем название фасета 
	select "name" into _facet_name_part
	from facetlar_v2
	where deal_type = p_deal_type 
		and offer_type = p_offer_type;
	
	-- объединяем в формат "Московская область::Квартира::Купить"
	o_facet_name := _region_name || '::' || _facet_name_part;
end;
$$ language plpgsql;
