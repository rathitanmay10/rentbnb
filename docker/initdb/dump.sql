--
-- PostgreSQL database dump
--

\restrict vObos2r1fedzK3qAVZ3PKW4gI3OxHofx77lkqZ47qsJV2R1QEFerviDr6jPB6Zg

-- Dumped from database version 14.19 (Homebrew)
-- Dumped by pg_dump version 14.19 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: btree_gist; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS btree_gist WITH SCHEMA public;


--
-- Name: EXTENSION btree_gist; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION btree_gist IS 'support for indexing common datatypes in GiST';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: amenities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.amenities (
    name character varying(255) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: blacklisted_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.blacklisted_tokens (
    user_id uuid NOT NULL,
    jti character varying(255) NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: bookings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bookings (
    property_id uuid NOT NULL,
    guest_id uuid NOT NULL,
    property_manager_id uuid NOT NULL,
    status character varying(9) NOT NULL,
    check_in date NOT NULL,
    check_out date NOT NULL,
    total_amount numeric(10,2) NOT NULL,
    commission_amount numeric(10,2) NOT NULL,
    cancelled_at timestamp with time zone,
    expires_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    tenant_id uuid NOT NULL,
    base_amount numeric(10,2) NOT NULL,
    CONSTRAINT check_in_before_check_out CHECK ((check_in < check_out)),
    CONSTRAINT commission_non_negative CHECK ((commission_amount >= (0)::numeric)),
    CONSTRAINT total_amount_non_negative CHECK ((total_amount >= (0)::numeric))
);


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    booking_id uuid NOT NULL,
    sender_id uuid,
    content text NOT NULL,
    message_type character varying(19) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    tenant_id uuid NOT NULL
);


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    booking_id uuid NOT NULL,
    guest_id uuid NOT NULL,
    status character varying(8) NOT NULL,
    amount numeric(10,2) NOT NULL,
    currency character varying(10) NOT NULL,
    razorpay_order_id character varying(255) NOT NULL,
    razorpay_payment_id character varying(255),
    razorpay_signature character varying(512),
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    tenant_id uuid NOT NULL,
    CONSTRAINT amount_non_negative CHECK ((amount >= (0)::numeric))
);


--
-- Name: properties; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.properties (
    managed_by uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    address character varying(255) NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(100) NOT NULL,
    country character varying(100) NOT NULL,
    zipcode character varying(20),
    latitude numeric(10,6) NOT NULL,
    longitude numeric(10,6) NOT NULL,
    category character varying(10) NOT NULL,
    bedrooms integer NOT NULL,
    max_guests integer NOT NULL,
    price_per_night numeric(10,2) NOT NULL,
    is_active boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean NOT NULL,
    deleted_at timestamp with time zone,
    tenant_id uuid NOT NULL,
    rating numeric(3,2) NOT NULL,
    review_count integer NOT NULL
);


--
-- Name: property_amenities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.property_amenities (
    property_id uuid NOT NULL,
    amenity_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: property_images; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.property_images (
    property_id uuid NOT NULL,
    url character varying(1024) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reviews (
    booking_id uuid NOT NULL,
    property_id uuid NOT NULL,
    guest_id uuid NOT NULL,
    rating integer NOT NULL,
    comment text,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    tenant_id uuid NOT NULL,
    CONSTRAINT rating_valid CHECK (((rating >= 1) AND (rating <= 5)))
);


--
-- Name: tenants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tenants (
    name character varying(255) NOT NULL,
    status character varying(8) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    username character varying(150) NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    token_version integer NOT NULL,
    role character varying(12) NOT NULL,
    tenant_id uuid,
    is_active boolean NOT NULL,
    is_verified boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    is_deleted boolean NOT NULL,
    deleted_at timestamp with time zone,
    first_name character varying(150),
    last_name character varying(150)
);


--
-- Name: webhooks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.webhooks (
    event_type character varying(100) NOT NULL,
    payload json NOT NULL,
    razorpay_event_id character varying(255) NOT NULL,
    processed boolean NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    tenant_id uuid
);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
32508009b2b0
\.


--
-- Data for Name: amenities; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.amenities (name, id, created_at, updated_at, is_deleted, deleted_at) FROM stdin;
wifi	6f5666cc-f416-4949-971a-5050920a38d8	2026-02-10 23:35:33.192474+05:30	2026-02-17 13:05:38.572428+05:30	f	\N
air conditioning	d93983cd-5424-460d-8196-ffca0e072a1b	2026-02-17 13:06:49.541248+05:30	2026-02-17 13:06:49.541248+05:30	f	\N
heating	d4283225-73e2-4698-8e25-cce297854266	2026-02-17 13:07:05.299059+05:30	2026-02-17 13:07:05.299059+05:30	f	\N
ceiling fan	9e5968d8-524d-4e95-be2b-438bb0e946f9	2026-02-17 13:07:12.516442+05:30	2026-02-17 13:07:12.516442+05:30	f	\N
refrigerator	29366fcf-94cf-4e28-a58a-d9c4403ba8e5	2026-02-17 13:07:40.9918+05:30	2026-02-17 13:07:40.9918+05:30	f	\N
balcony	a73da697-47a0-4092-8a8e-c2a2dab17634	2026-02-17 13:07:47.985584+05:30	2026-02-17 13:07:47.985584+05:30	f	\N
swimming pool	fff59205-eece-4624-99c1-f1619346f670	2026-02-17 13:07:57.459426+05:30	2026-02-17 13:07:57.459426+05:30	f	\N
\.


--
-- Data for Name: blacklisted_tokens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.blacklisted_tokens (user_id, jti, expires_at, id, created_at, updated_at, is_deleted, deleted_at) FROM stdin;
1f1f784d-e4e1-4c3f-a826-b602a9901f1f	a2b3ad3a-82db-4c7a-82ce-d09a9f07a958	2026-02-18 10:49:02+05:30	35cf7a34-8c49-4e9c-8400-a663891c34ea	2026-02-17 10:49:05.142047+05:30	2026-02-17 10:49:05.142047+05:30	f	\N
910b56bd-8538-4419-9dd9-a8512ca31f2e	fc8867ee-d55c-40ce-bad9-2e89fc81f3fc	2026-02-18 11:28:45+05:30	e0319b0c-d8be-44dd-9855-43182d9b42dc	2026-02-17 11:29:11.325311+05:30	2026-02-17 11:29:11.325311+05:30	f	\N
910b56bd-8538-4419-9dd9-a8512ca31f2e	c2d40e48-928b-4cae-af63-ed440dc5674f	2026-02-18 11:29:11+05:30	3548467d-2f51-4689-984e-9785fadb9e13	2026-02-17 11:29:24.508034+05:30	2026-02-17 11:29:24.508034+05:30	f	\N
910b56bd-8538-4419-9dd9-a8512ca31f2e	6d9224cc-65be-4a11-ab3c-cd11e59e3cc5	2026-02-18 11:33:58+05:30	e8202e04-3680-46d7-9ffc-fd4a75c7271f	2026-02-17 11:34:23.066049+05:30	2026-02-17 11:34:23.066049+05:30	f	\N
910b56bd-8538-4419-9dd9-a8512ca31f2e	4acb243c-4e20-48df-acb1-be7c53c10c53	2026-02-19 12:42:54+05:30	37a2006c-299e-4be7-8605-b0e6479b79e2	2026-02-18 12:43:01.32877+05:30	2026-02-18 12:43:01.32877+05:30	f	\N
\.


--
-- Data for Name: bookings; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.bookings (property_id, guest_id, property_manager_id, status, check_in, check_out, total_amount, commission_amount, cancelled_at, expires_at, id, created_at, updated_at, tenant_id, base_amount) FROM stdin;
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	b0b56560-0f6e-409e-95c5-9ed60548be28	CONFIRMED	2025-04-29	2025-04-30	550.00	50.00	\N	2026-02-16 12:38:35.1231+05:30	8bc0bfce-3d99-4d25-b687-f6414042c01b	2026-02-16 12:28:35.105098+05:30	2026-02-16 12:28:35.105098+05:30	ab657725-ae08-457a-a68b-8a64bd143146	500.00
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	b0b56560-0f6e-409e-95c5-9ed60548be28	CONFIRMED	2025-03-10	2025-03-20	5500.00	500.00	\N	2026-02-16 14:14:34.168261+05:30	377d2fc5-57f5-4cb8-8bdc-0840110abc45	2026-02-16 14:04:34.157372+05:30	2026-02-16 14:05:01.620814+05:30	ab657725-ae08-457a-a68b-8a64bd143146	5000.00
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	b0b56560-0f6e-409e-95c5-9ed60548be28	CONFIRMED	2026-02-26	2026-02-28	1100.00	100.00	\N	2026-02-16 18:49:49.819603+05:30	eb6436cf-0c2b-4ba8-b0a3-3ed98c96dd32	2026-02-16 18:39:49.799337+05:30	2026-02-16 18:40:01.725314+05:30	ab657725-ae08-457a-a68b-8a64bd143146	1000.00
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	b0b56560-0f6e-409e-95c5-9ed60548be28	CANCELLED	2026-03-04	2026-03-07	1650.00	150.00	2026-02-17 16:01:08.328238+05:30	2026-02-17 14:53:59.408884+05:30	daf5d818-5622-4d7c-9043-22e0cc392100	2026-02-17 14:43:59.34556+05:30	2026-02-17 16:01:08.205669+05:30	ab657725-ae08-457a-a68b-8a64bd143146	1500.00
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	b0b56560-0f6e-409e-95c5-9ed60548be28	CANCELLED	2026-03-04	2026-03-07	1650.00	150.00	2026-02-17 16:49:35.603333+05:30	2026-02-17 16:49:35.568937+05:30	a59b38d3-eab0-4d34-8a62-80879cff860f	2026-02-17 16:39:35.493865+05:30	2026-02-17 16:49:35.596488+05:30	ab657725-ae08-457a-a68b-8a64bd143146	1500.00
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	b0b56560-0f6e-409e-95c5-9ed60548be28	CANCELLED	2026-04-01	2026-04-10	4950.00	450.00	2026-02-17 16:52:12.568187+05:30	2026-02-17 16:52:12.535663+05:30	13a8edb2-769f-4eb1-8c61-3c691fa78f30	2026-02-17 16:42:12.52551+05:30	2026-02-17 16:52:12.562333+05:30	ab657725-ae08-457a-a68b-8a64bd143146	4500.00
40423840-4cfc-483d-8dc2-30dbd61135d3	4edc98d5-c71f-4593-aa5b-1c8ba2e2b6b4	d6658b77-b384-4557-8ebf-1681e8911d56	CONFIRMED	2026-02-26	2026-02-28	1100.00	100.00	\N	2026-02-17 17:37:00.292267+05:30	55b81660-7973-4db8-907b-21bb85414f8d	2026-02-17 17:27:00.281458+05:30	2026-02-17 17:27:09.09932+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	1000.00
40423840-4cfc-483d-8dc2-30dbd61135d3	4edc98d5-c71f-4593-aa5b-1c8ba2e2b6b4	d6658b77-b384-4557-8ebf-1681e8911d56	CONFIRMED	2026-03-12	2026-03-14	1100.00	100.00	\N	2026-02-17 22:24:29.880936+05:30	c6660d19-e647-4e4d-afe5-c741f139de5a	2026-02-17 22:14:29.871475+05:30	2026-02-17 22:14:42.712244+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	1000.00
40423840-4cfc-483d-8dc2-30dbd61135d3	4edc98d5-c71f-4593-aa5b-1c8ba2e2b6b4	d6658b77-b384-4557-8ebf-1681e8911d56	CANCELLED	2026-04-29	2026-04-30	550.00	50.00	2026-02-18 10:36:18.121183+05:30	2026-02-17 22:44:23.485567+05:30	390b31d1-9bb9-4910-9d31-9ed1a66d59f6	2026-02-17 22:34:23.478464+05:30	2026-02-18 10:36:18.11778+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	500.00
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	b0b56560-0f6e-409e-95c5-9ed60548be28	FAILED	2026-04-29	2026-04-30	550.00	50.00	\N	2026-02-18 10:44:45.742732+05:30	2ac6e547-0781-45e2-94cf-eecc2cc3ff71	2026-02-18 10:34:45.733802+05:30	2026-02-18 10:44:45.754518+05:30	ab657725-ae08-457a-a68b-8a64bd143146	500.00
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	d7b6ec8b-4d99-4544-a548-99817190b90e	b0b56560-0f6e-409e-95c5-9ed60548be28	CONFIRMED	2026-05-05	2026-05-13	4400.00	400.00	\N	2026-02-18 12:00:19.381841+05:30	e8f684c2-4969-49ce-a8d4-1df49ab8029a	2026-02-18 11:50:19.372512+05:30	2026-02-18 11:50:31.502023+05:30	ab657725-ae08-457a-a68b-8a64bd143146	4000.00
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	b0b56560-0f6e-409e-95c5-9ed60548be28	CANCELLED	2026-04-02	2026-04-10	4400.00	400.00	2026-02-18 17:28:10.894178+05:30	2026-02-18 17:36:36.658401+05:30	09275936-0907-413f-805e-5928905b8ce3	2026-02-18 17:26:36.649968+05:30	2026-02-18 17:28:10.871953+05:30	ab657725-ae08-457a-a68b-8a64bd143146	4000.00
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.messages (booking_id, sender_id, content, message_type, id, created_at, updated_at, tenant_id) FROM stdin;
377d2fc5-57f5-4cb8-8bdc-0840110abc45	\N	Booking confirmed! Payment successful.	SYSTEM_NOTIFICATION	eb421844-bff8-4a58-8eec-5fd05d5821b2	2026-02-16 14:05:01.620814+05:30	2026-02-16 14:05:01.620814+05:30	ab657725-ae08-457a-a68b-8a64bd143146
eb6436cf-0c2b-4ba8-b0a3-3ed98c96dd32	\N	Booking confirmed! Payment successful.	SYSTEM_NOTIFICATION	7049741a-b418-470f-8c80-4b40f3887a95	2026-02-16 18:40:01.725314+05:30	2026-02-16 18:40:01.725314+05:30	ab657725-ae08-457a-a68b-8a64bd143146
daf5d818-5622-4d7c-9043-22e0cc392100	\N	Booking confirmed! Payment successful.	SYSTEM_NOTIFICATION	18dcc728-d333-4ea7-9dac-80203403594d	2026-02-17 14:44:10.548707+05:30	2026-02-17 14:44:10.548707+05:30	ab657725-ae08-457a-a68b-8a64bd143146
daf5d818-5622-4d7c-9043-22e0cc392100	\N	Booking cancelled.	SYSTEM_NOTIFICATION	77e68dfd-3a5b-4ce5-9665-61261a926b68	2026-02-17 16:01:08.340589+05:30	2026-02-17 16:01:08.340589+05:30	ab657725-ae08-457a-a68b-8a64bd143146
a59b38d3-eab0-4d34-8a62-80879cff860f	\N	Booking expired.	SYSTEM_NOTIFICATION	6f4805cd-aa9a-4f60-8574-871a40c4b3c1	2026-02-17 16:49:35.620311+05:30	2026-02-17 16:49:35.620311+05:30	ab657725-ae08-457a-a68b-8a64bd143146
13a8edb2-769f-4eb1-8c61-3c691fa78f30	\N	Booking expired.	SYSTEM_NOTIFICATION	3403f3fa-7be1-4616-b27d-7fd73a78ef54	2026-02-17 16:52:12.581832+05:30	2026-02-17 16:52:12.581832+05:30	ab657725-ae08-457a-a68b-8a64bd143146
55b81660-7973-4db8-907b-21bb85414f8d	\N	Booking confirmed! Payment successful.	SYSTEM_NOTIFICATION	796c2d82-ab47-4db7-abb5-14d575a50b17	2026-02-17 17:27:09.09932+05:30	2026-02-17 17:27:09.09932+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca
c6660d19-e647-4e4d-afe5-c741f139de5a	\N	Booking confirmed! Payment successful.	SYSTEM_NOTIFICATION	d6701a30-26a7-452d-916f-dc780b765646	2026-02-17 22:14:42.712244+05:30	2026-02-17 22:14:42.712244+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca
c6660d19-e647-4e4d-afe5-c741f139de5a	4edc98d5-c71f-4593-aa5b-1c8ba2e2b6b4	Hi	USER_MESSAGE	bee8accd-4bed-4703-af35-1fa688e891c7	2026-02-17 22:32:49.402463+05:30	2026-02-17 22:32:49.402463+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca
390b31d1-9bb9-4910-9d31-9ed1a66d59f6	\N	Booking cancelled.	SYSTEM_NOTIFICATION	a988b44c-5d5d-424d-8524-0038b67ca842	2026-02-18 10:36:18.12754+05:30	2026-02-18 10:36:18.12754+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca
2ac6e547-0781-45e2-94cf-eecc2cc3ff71	\N	Booking expired.	SYSTEM_NOTIFICATION	6277e65c-26f6-4169-84bc-f6c4cf06dce5	2026-02-18 10:44:45.778893+05:30	2026-02-18 10:44:45.778893+05:30	ab657725-ae08-457a-a68b-8a64bd143146
2ac6e547-0781-45e2-94cf-eecc2cc3ff71	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	Hi, I have some questions regarding check in policy.	USER_MESSAGE	04b0336a-064b-491d-98f9-29a41b6bf2a7	2026-02-18 11:41:49.18031+05:30	2026-02-18 11:41:49.18031+05:30	ab657725-ae08-457a-a68b-8a64bd143146
2ac6e547-0781-45e2-94cf-eecc2cc3ff71	910b56bd-8538-4419-9dd9-a8512ca31f2e	Can you specify your doubts?	USER_MESSAGE	7c9e53ea-3918-45b0-8baf-8055b560f745	2026-02-18 11:42:34.695116+05:30	2026-02-18 11:42:34.695116+05:30	ab657725-ae08-457a-a68b-8a64bd143146
2ac6e547-0781-45e2-94cf-eecc2cc3ff71	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	Is there specified time for check in and check out?	USER_MESSAGE	7786a39b-6089-4572-a952-4d3c893ee438	2026-02-18 11:42:20.448292+05:30	2026-02-18 11:42:20.448292+05:30	ab657725-ae08-457a-a68b-8a64bd143146
e8f684c2-4969-49ce-a8d4-1df49ab8029a	\N	Booking confirmed! Payment successful.	SYSTEM_NOTIFICATION	d2de0897-1347-4da6-9039-254948895182	2026-02-18 11:50:31.502023+05:30	2026-02-18 11:50:31.502023+05:30	ab657725-ae08-457a-a68b-8a64bd143146
2ac6e547-0781-45e2-94cf-eecc2cc3ff71	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	hi	USER_MESSAGE	ee27dbfe-7e70-4be5-a72b-4c07f6ff8340	2026-02-18 17:20:40.300872+05:30	2026-02-18 17:20:40.300872+05:30	ab657725-ae08-457a-a68b-8a64bd143146
2ac6e547-0781-45e2-94cf-eecc2cc3ff71	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	Check in times?	USER_MESSAGE	305b0296-925a-4892-b2e2-d8765362a5fe	2026-02-18 17:21:58.135367+05:30	2026-02-18 17:21:58.135367+05:30	ab657725-ae08-457a-a68b-8a64bd143146
09275936-0907-413f-805e-5928905b8ce3	\N	Booking confirmed! Payment successful.	SYSTEM_NOTIFICATION	84a8a929-cf47-4a8d-b155-7618d53fd808	2026-02-18 17:26:49.299258+05:30	2026-02-18 17:26:49.299258+05:30	ab657725-ae08-457a-a68b-8a64bd143146
09275936-0907-413f-805e-5928905b8ce3	\N	Booking cancelled.	SYSTEM_NOTIFICATION	aa249a24-733b-401b-8ba5-6c59ea16a363	2026-02-18 17:28:10.89883+05:30	2026-02-18 17:28:10.89883+05:30	ab657725-ae08-457a-a68b-8a64bd143146
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.payments (booking_id, guest_id, status, amount, currency, razorpay_order_id, razorpay_payment_id, razorpay_signature, id, created_at, updated_at, tenant_id) FROM stdin;
377d2fc5-57f5-4cb8-8bdc-0840110abc45	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	PAID	5500.00	INR	order_SGkk2iQ8JNLc2C	pay_SGkkE92dZqNcmh	\N	29ff528f-e71d-461b-9479-d1090d411307	2026-02-16 14:04:34.179042+05:30	2026-02-16 14:05:01.620814+05:30	ab657725-ae08-457a-a68b-8a64bd143146
eb6436cf-0c2b-4ba8-b0a3-3ed98c96dd32	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	PAID	1100.00	INR	order_SGpQoLCkRnZ1u1	pay_SGpQzCaRvg7b8L	\N	fb911d4e-796c-4736-a62b-e4afad3486b5	2026-02-16 18:39:49.829878+05:30	2026-02-16 18:40:01.725314+05:30	ab657725-ae08-457a-a68b-8a64bd143146
8bc0bfce-3d99-4d25-b687-f6414042c01b	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	PAID	550.00	INR	order_SGj6eUqxiZt91r	\N	\N	a4be3cf6-35ec-437a-8a76-960a6fabf58a	2026-02-16 12:28:35.134984+05:30	2026-02-16 12:28:35.134984+05:30	ab657725-ae08-457a-a68b-8a64bd143146
daf5d818-5622-4d7c-9043-22e0cc392100	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	REFUNDED	1650.00	INR	order_SH9wnv3G2N2zuX	pay_SH9wy5agswS2ze	\N	5bf5a925-b67f-4f8d-b7a5-1fa8935963e2	2026-02-17 14:43:59.421217+05:30	2026-02-17 16:01:08.340809+05:30	ab657725-ae08-457a-a68b-8a64bd143146
a59b38d3-eab0-4d34-8a62-80879cff860f	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	PENDING	1650.00	INR	order_SHBuv4i7H2g12o	\N	\N	aed57de4-a66b-473b-a73d-513518f3e119	2026-02-17 16:39:35.579572+05:30	2026-02-17 16:39:35.579572+05:30	ab657725-ae08-457a-a68b-8a64bd143146
13a8edb2-769f-4eb1-8c61-3c691fa78f30	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	FAILED	4950.00	INR	order_SHBxgOX8SiFsng	\N	\N	a7607d87-b906-4105-8c0c-54d7707a7264	2026-02-17 16:42:12.545993+05:30	2026-02-17 16:42:47.763467+05:30	ab657725-ae08-457a-a68b-8a64bd143146
55b81660-7973-4db8-907b-21bb85414f8d	4edc98d5-c71f-4593-aa5b-1c8ba2e2b6b4	PAID	1100.00	INR	order_SHCj0AMFBWvDa5	pay_SHCj7lgubtPbqx	\N	36356767-a930-4235-937c-7b73b6421646	2026-02-17 17:27:00.300978+05:30	2026-02-17 17:27:09.09932+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca
c6660d19-e647-4e4d-afe5-c741f139de5a	4edc98d5-c71f-4593-aa5b-1c8ba2e2b6b4	PAID	1100.00	INR	order_SHHch1XC9Hlg17	pay_SHHcsxatG9Q6x7	\N	4e8a0a47-d042-416d-8e8c-bcacbdee3bcc	2026-02-17 22:14:29.8891+05:30	2026-02-17 22:14:42.712244+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca
390b31d1-9bb9-4910-9d31-9ed1a66d59f6	4edc98d5-c71f-4593-aa5b-1c8ba2e2b6b4	PENDING	550.00	INR	order_SHHxhfcMad5W5E	\N	\N	9ca138d2-59b1-42f3-9b94-7f1380ab6528	2026-02-17 22:34:23.493566+05:30	2026-02-17 22:34:23.493566+05:30	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca
2ac6e547-0781-45e2-94cf-eecc2cc3ff71	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	PENDING	550.00	INR	order_SHUEewBuvqKx4d	\N	\N	3b91d4e5-a197-4015-b764-40534ac7ed00	2026-02-18 10:34:45.756641+05:30	2026-02-18 10:34:45.756641+05:30	ab657725-ae08-457a-a68b-8a64bd143146
e8f684c2-4969-49ce-a8d4-1df49ab8029a	d7b6ec8b-4d99-4544-a548-99817190b90e	PAID	4400.00	INR	order_SHVWTZPhSs6ACT	pay_SHVWekodXFVFBy	\N	28ee73e4-4779-47ad-8bdf-dc63457e4964	2026-02-18 11:50:19.389406+05:30	2026-02-18 11:50:31.502023+05:30	ab657725-ae08-457a-a68b-8a64bd143146
09275936-0907-413f-805e-5928905b8ce3	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	PAID	4400.00	INR	order_SHbFhyDxHiSGVA	pay_SHbFtmFCFRQC6T	\N	84ab56bf-1d1a-407e-839f-a86cdd1fca48	2026-02-18 17:26:36.668186+05:30	2026-02-18 17:26:49.299258+05:30	ab657725-ae08-457a-a68b-8a64bd143146
\.


--
-- Data for Name: properties; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.properties (managed_by, name, description, address, city, state, country, zipcode, latitude, longitude, category, bedrooms, max_guests, price_per_night, is_active, id, created_at, updated_at, is_deleted, deleted_at, tenant_id, rating, review_count) FROM stdin;
b2d267da-5779-4b2b-ab1c-d47948a1a0db	string	string	string	string	string	string	string	-90.000000	-180.000000	APARTMENT	1	1	1.00	t	57064847-5499-4329-9a94-880ac654da5a	2026-02-18 15:35:12.493251+05:30	2026-02-18 15:35:53.667286+05:30	t	2026-02-18 15:35:53.671521+05:30	ab657725-ae08-457a-a68b-8a64bd143146	0.00	0
b2d267da-5779-4b2b-ab1c-d47948a1a0db	string	string	string	string	string	string	string	-90.000000	-180.000000	APARTMENT	1	1	1.00	t	fcf8d8c8-e43b-42e8-8ef1-a6a08acbf6da	2026-02-18 15:36:44.619103+05:30	2026-02-18 15:38:11.991281+05:30	t	2026-02-18 15:38:11.995374+05:30	ab657725-ae08-457a-a68b-8a64bd143146	0.00	0
d6658b77-b384-4557-8ebf-1681e8911d56	Natraj PG (Tenant 2)	At Shiv Darshan Boys Hostel And Pg, guests are provided with a secure and welcoming environment featuring modern amenities and personalized services. Offering flexible living arrangements, Shiv Darshan Boys Hostel And Pg ensures that every guest finds the perfect fit for their needs.	38, Manayak colony, behind st. gregrious school, New Bhupalpura, Pahada	Udaipur	Rajasthan	India	313001	24.597644	73.710075	DORM	7	10	500.00	t	40423840-4cfc-483d-8dc2-30dbd61135d3	2026-02-17 16:56:20.122086+05:30	2026-02-17 16:56:20.122086+05:30	f	\N	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	0.00	0
65fbf69a-44e2-4d58-ac84-cb753f906dcc	Ram PG	\N	103, Rani Road	Udaipur	Rajasthan	India	313001	-20.666667	-130.444444	APARTMENT	1	1	500.00	t	4336077c-09b6-4242-965b-d94f2082026f	2026-02-18 17:08:46.674979+05:30	2026-02-18 17:08:46.674979+05:30	f	\N	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	0.00	0
b0b56560-0f6e-409e-95c5-9ed60548be28	Natraj PG	At Shiv Darshan Boys Hostel And Pg, guests are provided with a secure and welcoming environment featuring modern amenities and personalized services. Offering flexible living arrangements, Shiv Darshan Boys Hostel And Pg ensures that every guest finds the perfect fit for their needs.	38, Manayak colony, behind st. gregrious school, New Bhupalpura, Pahada	Udaipur	Rajasthan	India	313001	24.597644	73.710076	DORM	6	10	500.00	t	c30f5707-5e50-4c4f-afe5-36dfae9a46ff	2026-02-15 23:07:40.847313+05:30	2026-02-18 17:30:42.60232+05:30	f	\N	ab657725-ae08-457a-a68b-8a64bd143146	4.00	2
\.


--
-- Data for Name: property_amenities; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.property_amenities (property_id, amenity_id, id, created_at, updated_at) FROM stdin;
40423840-4cfc-483d-8dc2-30dbd61135d3	d93983cd-5424-460d-8196-ffca0e072a1b	d002623e-d10a-496d-9ec4-6ce40a81bc58	2026-02-18 10:37:40.44326+05:30	2026-02-18 10:37:40.44326+05:30
40423840-4cfc-483d-8dc2-30dbd61135d3	6f5666cc-f416-4949-971a-5050920a38d8	5ca1ffd7-6669-4962-aed7-d827798922c3	2026-02-18 10:37:40.44326+05:30	2026-02-18 10:37:40.44326+05:30
40423840-4cfc-483d-8dc2-30dbd61135d3	d4283225-73e2-4698-8e25-cce297854266	8909a502-5cc5-4f83-b3e9-a27578efacf6	2026-02-18 10:37:40.44326+05:30	2026-02-18 10:37:40.44326+05:30
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	d4283225-73e2-4698-8e25-cce297854266	19f2cf84-69d0-40b9-b9c8-4fb3fbfd59cd	2026-02-18 12:20:13.353163+05:30	2026-02-18 12:20:13.353163+05:30
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	d93983cd-5424-460d-8196-ffca0e072a1b	f510c832-ef19-482f-85b0-3226f9c58ada	2026-02-18 12:20:13.353163+05:30	2026-02-18 12:20:13.353163+05:30
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	6f5666cc-f416-4949-971a-5050920a38d8	e12b6bda-55f0-4655-ab28-2e57f11850dd	2026-02-18 12:20:31.332169+05:30	2026-02-18 12:20:31.332169+05:30
\.


--
-- Data for Name: property_images; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.property_images (property_id, url, id, created_at, updated_at, is_deleted, deleted_at) FROM stdin;
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	/uploads/c30f5707-5e50-4c4f-afe5-36dfae9a46ff/ca1566c2-7291-4171-9db4-910865b5f061.png	28b0718b-1855-4670-a9e3-efb6b09d88e8	2026-02-15 23:12:35.078482+05:30	2026-02-15 23:12:35.078482+05:30	f	\N
40423840-4cfc-483d-8dc2-30dbd61135d3	/uploads/40423840-4cfc-483d-8dc2-30dbd61135d3/46cde851-184b-40db-875d-2666e48e5fb2.png	22c9b9fd-268f-44cb-8c14-603f9caae0e2	2026-02-17 17:09:31.184526+05:30	2026-02-17 17:09:31.184526+05:30	f	\N
c30f5707-5e50-4c4f-afe5-36dfae9a46ff	/uploads/c30f5707-5e50-4c4f-afe5-36dfae9a46ff/19a894a8-0503-4ff8-a5d1-b7ca032ad04d.png	bf01ce41-8ad0-4a75-8b80-34c5424b8d77	2026-02-18 14:52:12.598281+05:30	2026-02-18 14:52:12.598281+05:30	f	\N
4336077c-09b6-4242-965b-d94f2082026f	/uploads/4336077c-09b6-4242-965b-d94f2082026f/e7f22f16-b580-4404-bb6e-8fdcbc9f18a7.png	85b2d1bc-4da3-44e7-92db-0b1a47f112fd	2026-02-18 17:11:07.146466+05:30	2026-02-18 17:11:07.146466+05:30	f	\N
\.


--
-- Data for Name: reviews; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.reviews (booking_id, property_id, guest_id, rating, comment, id, created_at, updated_at, tenant_id) FROM stdin;
377d2fc5-57f5-4cb8-8bdc-0840110abc45	c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	3	Good Service	8df063a4-98b3-47be-b4a2-d9afcd394151	2026-02-16 14:08:13.555164+05:30	2026-02-18 12:10:46.754712+05:30	ab657725-ae08-457a-a68b-8a64bd143146
8bc0bfce-3d99-4d25-b687-f6414042c01b	c30f5707-5e50-4c4f-afe5-36dfae9a46ff	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	5	\N	665e214b-ece9-413a-b7d8-2c82fc2b119d	2026-02-18 17:30:42.60232+05:30	2026-02-18 17:30:42.60232+05:30	ab657725-ae08-457a-a68b-8a64bd143146
\.


--
-- Data for Name: tenants; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tenants (name, status, id, created_at, updated_at, is_deleted, deleted_at) FROM stdin;
tenant 2	ACTIVE	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	2026-02-09 18:43:00.44764+05:30	2026-02-09 18:43:00.44764+05:30	f	\N
tenant 3	ACTIVE	5f79cf64-554e-4845-9ca4-9ba622b473c3	2026-02-10 16:43:37.226412+05:30	2026-02-10 16:46:51.928759+05:30	f	\N
tenant 1	ACTIVE	ab657725-ae08-457a-a68b-8a64bd143146	2026-02-09 17:10:50.673319+05:30	2026-02-17 11:08:29.236673+05:30	f	\N
tenant 4	INACTIVE	ed4ce5df-043f-4a61-8d8f-b7fe08d9f56d	2026-02-10 22:09:56.67084+05:30	2026-02-17 11:48:29.119804+05:30	t	2026-02-17 11:48:29.127628+05:30
tenant 5	ACTIVE	71936d39-4d83-4a52-a98a-f2bfc143a678	2026-02-17 11:57:03.291+05:30	2026-02-17 11:57:03.291+05:30	f	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (username, email, hashed_password, token_version, role, tenant_id, is_active, is_verified, id, created_at, updated_at, is_deleted, deleted_at, first_name, last_name) FROM stdin;
tanmay1	rohan@yopmail.com	$2b$12$VlMfDzEuiKPI6vuOr4Mare74aYx2IvEqKUNQWP.2zKpb6vs.gueS.	1	GUEST	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	t	t	14d21cca-78fb-47f2-acb0-d6bf332234a3	2026-02-17 11:12:17.961747+05:30	2026-02-17 11:12:57.709407+05:30	f	\N	\N	\N
manager1	manager1@yopmail.com	$2b$12$o9oS5ZwLND0Iit1JOAdvXe/pPTK.662lhY150As2LXYfFx/UxU/fG	1	MANAGER	ab657725-ae08-457a-a68b-8a64bd143146	t	t	b0b56560-0f6e-409e-95c5-9ed60548be28	2026-02-10 12:16:13.372838+05:30	2026-02-10 12:16:13.372838+05:30	f	\N	\N	\N
admin4	admin4@yopmail.com	$2b$12$jyHgTTuefCFj5w.pcEPEDe0PagBVAePdK8Q0BFiqFy8td5QXbdOIG	1	TENANT_ADMIN	ed4ce5df-043f-4a61-8d8f-b7fe08d9f56d	t	t	caa4d19e-cfe8-4bf0-ae6d-3364bf5f9d89	2026-02-10 22:09:56.67084+05:30	2026-02-17 11:48:29.119804+05:30	t	2026-02-17 11:48:29.122861+05:30	\N	\N
admin3	admin3@yopmail.com	$2b$12$oTJkST2G2LfQsfhu2cvxW.OfacimGEWCinNdW.C2LE1DDhRBPbV/q	1	TENANT_ADMIN	5f79cf64-554e-4845-9ca4-9ba622b473c3	t	t	c7a6bafb-f40d-4a2b-b35f-6a5d024c8d65	2026-02-10 22:12:44.194391+05:30	2026-02-10 22:13:35.138212+05:30	f	\N	\N	\N
amit1	amit@yopmail.com	$2b$12$tJJuvhLGdQPQuysL.kU68u62LPRU5ybQy1W90sC7AwBSO0NtFt8t2	1	GUEST	ab657725-ae08-457a-a68b-8a64bd143146	t	t	d7b6ec8b-4d99-4544-a548-99817190b90e	2026-02-11 15:33:34.576461+05:30	2026-02-11 15:33:57.327068+05:30	f	\N	\N	\N
admin2	admin2@yopmail.com	$2b$12$EtDBHd3WEr8lne0NgsfoneNrQnJt6vbLU30ZsCCyyFcoPpRHtxvGW	2	TENANT_ADMIN	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	t	t	65fbf69a-44e2-4d58-ac84-cb753f906dcc	2026-02-09 18:43:00.44764+05:30	2026-02-11 15:40:49.846217+05:30	f	\N	\N	\N
amit2	amit@yopmail.com	$2b$12$YsRaNRavLQ5n5WJmlaqGl.ZsQUKhUX0sBTp5pDauqewxboSWD62Um	1	GUEST	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	t	t	06a35b36-ded4-40e9-8496-83645bc41d32	2026-02-11 15:43:26.643336+05:30	2026-02-11 15:44:44.679834+05:30	f	\N	\N	\N
tanmay2	tanmay@yopmail.com	$2b$12$K3/K7AGQIgXl7nJwWcG2HeoKi.QKcLAU66PUwTGTilMB5DAON.Fny	1	GUEST	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	t	t	4edc98d5-c71f-4593-aa5b-1c8ba2e2b6b4	2026-02-11 15:45:11.8826+05:30	2026-02-11 15:48:07.772962+05:30	f	\N	\N	\N
tanmay1	tanmay@yopmail.com	$2b$12$EPJbjoC9E.zyMl8l8f3HmOVnH4E.WaeHLKj9VJbAcskgR48gVvWPK	1	GUEST	71936d39-4d83-4a52-a98a-f2bfc143a678	t	t	61fc09d9-40d8-4b0e-9567-647455a1e9aa	2026-02-17 12:03:41.699626+05:30	2026-02-17 12:51:23.306647+05:30	f	\N	Tanmay	
superadmin	superadmin@yopmail.com	$2b$12$slnKYD5lhkONU9sRu32qYuaj.YxBCCE62/i.76kthEs1h1o1oMg9K	1	SUPER_ADMIN	\N	t	t	d1850bc6-cde0-43a0-ad43-0d8badda9aac	2026-02-09 17:02:45.753253+05:30	2026-02-17 12:51:48.62973+05:30	f	\N	Super	Admin
manager1	manager1@yopmail.com	$2b$12$N4bTX1z8Z0YUXYykFM6xgOKP9an1qSLXTJR/uWuk/V5rqmbnzoTTO	1	MANAGER	71936d39-4d83-4a52-a98a-f2bfc143a678	f	f	02d9781b-ced5-47e7-843b-b3c68745fed6	2026-02-17 12:58:58.509683+05:30	2026-02-17 12:58:58.509683+05:30	f	\N	\N	\N
manager1	manager1@yopmail.com	$2b$12$JTG5dxnG.aRTTw4GYjKIPuGsl2hzSdjQzyuof3otpVcAWq4mFTDQW	1	MANAGER	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	t	t	d6658b77-b384-4557-8ebf-1681e8911d56	2026-02-17 16:53:33.435221+05:30	2026-02-17 16:55:28.511763+05:30	f	\N	\N	\N
manager2	manager2@yopmail.com	$2b$12$M/YIBU0IRzypq/n6vX/8b.odAxPIYns2YKWmxa4Iv/ojFlBj2P20.	1	MANAGER	ab657725-ae08-457a-a68b-8a64bd143146	t	t	b2d267da-5779-4b2b-ab1c-d47948a1a0db	2026-02-18 10:56:24.408981+05:30	2026-02-18 10:57:04.142653+05:30	f	\N	\N	\N
tanmay1	tanmay@yopmail.com	$2b$12$Iq.o7BxK9dQvLA2doj/.GOQXX6nEH9eT1JXRNEKRbLGe8tOlxxJ2q	1	GUEST	ab657725-ae08-457a-a68b-8a64bd143146	t	t	1f1f784d-e4e1-4c3f-a826-b602a9901f1f	2026-02-11 15:28:12.455878+05:30	2026-02-18 12:03:56.704642+05:30	f	\N	Tanmay	Rathi
string	user@example.com	$2b$12$UNOzHtX3x300ZTuGQMDv8.EN63t04UXUuYdjVkb2cG44PB8XFSTRu	1	GUEST	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	f	f	7f094e44-6b19-423a-ae47-9844e5b34fa4	2026-02-18 16:48:30.698776+05:30	2026-02-18 16:48:30.698776+05:30	f	\N	string	string
rohan1	rohan1@yopmail.com	$2b$12$dnpApG0dO1JkvVdRZH2c8ORb79LRDw4abaa8Q3kXBRYfOsGabDDXu	1	GUEST	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	t	t	f7fef623-6517-4255-b9f4-f67017fdc9f9	2026-02-18 16:49:27.02054+05:30	2026-02-18 16:50:00.051268+05:30	f	\N	\N	\N
rohan2	rohan2@yopmail.com	$2b$12$Mi9DzzqGQejlAFvAS3TqguccBf./yVl6nlWOmLHAYH2bJLS91GSia	1	GUEST	1b3f6411-a0c9-4922-9395-ab1e4dcb4fca	f	f	913bb5c7-75f6-449f-9650-15fb22042e14	2026-02-18 17:00:18.530434+05:30	2026-02-18 17:00:18.530434+05:30	f	\N	\N	\N
admin1	admin1@yopmail.com	$2b$12$DJ5spktPXGGD5BigtcvEYO3u8noOIh54J96ll1ush.NWpzFpq7D9q	4	TENANT_ADMIN	ab657725-ae08-457a-a68b-8a64bd143146	t	t	910b56bd-8538-4419-9dd9-a8512ca31f2e	2026-02-09 17:10:50.673319+05:30	2026-02-18 16:56:53.394174+05:30	f	\N	\N	\N
\.


--
-- Data for Name: webhooks; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.webhooks (event_type, payload, razorpay_event_id, processed, id, created_at, updated_at, tenant_id) FROM stdin;
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFWeTbuZZ4xH9T", "entity": "payment", "amount": 100000, "currency": "INR", "status": "captured", "order_id": "order_SFWeGna6kuFKgc", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "978cc362-aa38-4f9e-8542-36cf21383d83"}, "fee": 2360, "tax": 360, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "118168085873", "upi_transaction_id": "FD33BE8CD9568029C9C360B373DFE2C8"}, "created_at": 1770962916, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 100000}}}, "created_at": 1770962917}	SFWeVPZvugESBn	t	2306235e-4921-4c8b-adcb-2a3019c9e472	2026-02-13 11:39:12.897633+05:30	2026-02-13 11:39:12.921469+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFWiBM6nNUQLjP", "entity": "payment", "amount": 100000, "currency": "INR", "status": "authorized", "order_id": "order_SFWi5XGhsP7Enm", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "efe06f35-6635-4a39-93fa-43bbf30c5300"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "799858917773", "upi_transaction_id": "822AF6D8AF3C27975513DA3E6D45A5CA"}, "created_at": 1770963126, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1770963126}	SFWiCIQw3zBnsP	t	42c37253-47cb-4d20-acb3-e85d6e43cc3f	2026-02-13 11:42:07.047216+05:30	2026-02-13 11:42:07.051499+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFWeTbuZZ4xH9T", "entity": "payment", "amount": 100000, "currency": "INR", "status": "authorized", "order_id": "order_SFWeGna6kuFKgc", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "978cc362-aa38-4f9e-8542-36cf21383d83"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "118168085873", "upi_transaction_id": "FD33BE8CD9568029C9C360B373DFE2C8"}, "created_at": 1770962916, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1770962916}	SFWeUdt4sm2vTc	t	3b2a7170-9d1f-4279-bb6c-967a52c1145b	2026-02-13 11:39:11.843306+05:30	2026-02-13 11:39:11.85042+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFafHG6SlAt050", "entity": "payment", "amount": 350000, "currency": "INR", "status": "authorized", "order_id": "order_SFaf8PgAp2NYQP", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "396b716f-117f-4f1b-8551-a6d6ba7353f3"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "340348433630", "upi_transaction_id": "F7BBB5C21C6F1651AE53BB81A6975619"}, "created_at": 1770977047, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1770977048}	SFafIN7OKjWbpO	t	4e7415c0-fa37-4dc6-9bba-4d1ae2e5ba7f	2026-02-13 15:34:08.690051+05:30	2026-02-13 15:34:08.69878+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFafHG6SlAt050", "entity": "payment", "amount": 350000, "currency": "INR", "status": "captured", "order_id": "order_SFaf8PgAp2NYQP", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "396b716f-117f-4f1b-8551-a6d6ba7353f3"}, "fee": 8260, "tax": 1260, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "340348433630", "upi_transaction_id": "F7BBB5C21C6F1651AE53BB81A6975619"}, "created_at": 1770977047, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 350000}}}, "created_at": 1770977049}	SFafJ1mDRiO2ti	t	7d048bcb-7492-4b8f-950e-9d3126dd8c28	2026-02-13 15:34:09.228312+05:30	2026-02-13 15:34:09.259925+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFWiBM6nNUQLjP", "entity": "payment", "amount": 100000, "currency": "INR", "status": "captured", "order_id": "order_SFWi5XGhsP7Enm", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "efe06f35-6635-4a39-93fa-43bbf30c5300"}, "fee": 2360, "tax": 360, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "799858917773", "upi_transaction_id": "822AF6D8AF3C27975513DA3E6D45A5CA"}, "created_at": 1770963126, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 100000}}}, "created_at": 1770963127}	SFWiCxbNzQkyNI	t	d5f6bee4-1e1c-4898-9ecb-a04022f96ada	2026-02-13 11:42:07.695558+05:30	2026-02-13 11:42:07.70997+05:30	\N
refund.processed	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1770963190, "entity": "event", "event": "refund.processed", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "799858917773", "upi_transaction_id": "822AF6D8AF3C27975513DA3E6D45A5CA"}, "amount": 100000, "amount_refunded": 100000, "amount_transferred": 0, "bank": null, "base_amount": 100000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1770963126, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 2360, "id": "pay_SFWiBM6nNUQLjP", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "efe06f35-6635-4a39-93fa-43bbf30c5300"}, "order_id": "order_SFWi5XGhsP7Enm", "refund_status": "full", "status": "refunded", "tax": 360, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 100000, "batch_id": null, "created_at": 1770963186, "currency": "INR", "entity": "refund", "id": "rfnd_SFWjFhPOgdlaHu", "notes": [], "payment_id": "pay_SFWiBM6nNUQLjP", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFWjnk2R5x0ym7	t	1ace79b0-efa3-4b3f-807a-ec675b97d7b3	2026-02-13 11:43:38.159687+05:30	2026-02-13 11:43:38.164066+05:30	\N
refund.created	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1770963190, "entity": "event", "event": "refund.created", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "799858917773", "upi_transaction_id": "822AF6D8AF3C27975513DA3E6D45A5CA"}, "amount": 100000, "amount_refunded": 100000, "amount_transferred": 0, "bank": null, "base_amount": 100000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1770963126, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 2360, "id": "pay_SFWiBM6nNUQLjP", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "efe06f35-6635-4a39-93fa-43bbf30c5300"}, "order_id": "order_SFWi5XGhsP7Enm", "refund_status": "full", "status": "refunded", "tax": 360, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 100000, "batch_id": null, "created_at": 1770963186, "currency": "INR", "entity": "refund", "id": "rfnd_SFWjFhPOgdlaHu", "notes": [], "payment_id": "pay_SFWiBM6nNUQLjP", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFWjnfz69UeZho	t	2bba2753-8033-4f8b-b7cc-30944ca1de68	2026-02-13 11:43:38.164463+05:30	2026-02-13 11:43:38.173746+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFZsUer8ABm9TZ", "entity": "payment", "amount": 350000, "currency": "INR", "status": "authorized", "order_id": "order_SFZs9PIAzNwbhm", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "9b7b6865-9201-414a-ba7b-ad3b7acc71d4"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "743788553724", "upi_transaction_id": "8CF75A8EBEC10B51E7D6BE883CACFA24"}, "created_at": 1770974277, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1770974277}	SFZsVrTHPUIFmJ	t	35860cb6-8e9d-4dba-b8f2-3fac232f37b2	2026-02-13 14:47:57.773568+05:30	2026-02-13 14:47:57.782137+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFZsUer8ABm9TZ", "entity": "payment", "amount": 350000, "currency": "INR", "status": "captured", "order_id": "order_SFZs9PIAzNwbhm", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "9b7b6865-9201-414a-ba7b-ad3b7acc71d4"}, "fee": 8260, "tax": 1260, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "743788553724", "upi_transaction_id": "8CF75A8EBEC10B51E7D6BE883CACFA24"}, "created_at": 1770974277, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 350000}}}, "created_at": 1770974278}	SFZsWfLonWNMTn	t	253d0833-3675-44e2-990c-e682186b865a	2026-02-13 14:47:58.589658+05:30	2026-02-13 14:48:13.853391+05:30	\N
refund.processed	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1770974624, "entity": "event", "event": "refund.processed", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "743788553724", "upi_transaction_id": "8CF75A8EBEC10B51E7D6BE883CACFA24"}, "amount": 350000, "amount_refunded": 350000, "amount_transferred": 0, "bank": null, "base_amount": 350000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1770974277, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 8260, "id": "pay_SFZsUer8ABm9TZ", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "9b7b6865-9201-414a-ba7b-ad3b7acc71d4"}, "order_id": "order_SFZs9PIAzNwbhm", "refund_status": "full", "status": "refunded", "tax": 1260, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 350000, "batch_id": null, "created_at": 1770974621, "currency": "INR", "entity": "refund", "id": "rfnd_SFZyYZ2MOoaZiO", "notes": [], "payment_id": "pay_SFZsUer8ABm9TZ", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFZz6XrQe3eShW	t	4470f7f5-982b-4655-9d34-6ea74f4d4fb6	2026-02-13 14:54:12.141132+05:30	2026-02-13 14:54:12.150525+05:30	\N
refund.created	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1770974624, "entity": "event", "event": "refund.created", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "743788553724", "upi_transaction_id": "8CF75A8EBEC10B51E7D6BE883CACFA24"}, "amount": 350000, "amount_refunded": 350000, "amount_transferred": 0, "bank": null, "base_amount": 350000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1770974277, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 8260, "id": "pay_SFZsUer8ABm9TZ", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "9b7b6865-9201-414a-ba7b-ad3b7acc71d4"}, "order_id": "order_SFZs9PIAzNwbhm", "refund_status": "full", "status": "refunded", "tax": 1260, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 350000, "batch_id": null, "created_at": 1770974621, "currency": "INR", "entity": "refund", "id": "rfnd_SFZyYZ2MOoaZiO", "notes": [], "payment_id": "pay_SFZsUer8ABm9TZ", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFZz6YR8R0zwej	t	cfc14119-4cb2-4e77-9fbe-bf35600ab577	2026-02-13 14:54:12.175082+05:30	2026-02-13 14:54:12.178377+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFEL8CMrp7lO92", "entity": "payment", "amount": 1000000, "currency": "INR", "status": "captured", "order_id": "order_SFEKILybdhWGm0", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "34856fa9-e02f-47f0-8550-a7d499e319f7"}, "fee": 23600, "tax": 3600, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "375830622793", "upi_transaction_id": "284E244EA3BEB9A196163B5DE13D6F5D"}, "created_at": 1770898428, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 1000000}}}, "created_at": 1770898429}	SFEL9qfsuV8pAO	t	bdcbe4fa-4f29-43a0-a1da-7f39c416fbf2	2026-02-13 16:34:46.821659+05:30	2026-02-13 16:34:46.830458+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFEL8CMrp7lO92", "entity": "payment", "amount": 1000000, "currency": "INR", "status": "authorized", "order_id": "order_SFEKILybdhWGm0", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "34856fa9-e02f-47f0-8550-a7d499e319f7"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "375830622793", "upi_transaction_id": "284E244EA3BEB9A196163B5DE13D6F5D"}, "created_at": 1770898428, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1770898428}	SFEL9AUFrS3TQ4	t	2269c68f-b992-4f2a-8389-011ac2b74ade	2026-02-13 16:34:46.972799+05:30	2026-02-13 16:34:47.04942+05:30	\N
refund.created	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1770898473, "entity": "event", "event": "refund.created", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "375830622793", "upi_transaction_id": "284E244EA3BEB9A196163B5DE13D6F5D"}, "amount": 1000000, "amount_refunded": 1000000, "amount_transferred": 0, "bank": null, "base_amount": 1000000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1770898428, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 23600, "id": "pay_SFEL8CMrp7lO92", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "34856fa9-e02f-47f0-8550-a7d499e319f7"}, "order_id": "order_SFEKILybdhWGm0", "refund_status": "full", "status": "refunded", "tax": 3600, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 1000000, "batch_id": null, "created_at": 1770898470, "currency": "INR", "entity": "refund", "id": "rfnd_SFELsdLUWlfufl", "notes": [], "payment_id": "pay_SFEL8CMrp7lO92", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFEMQcABfR9Qfj	t	7a12a640-e9f5-46a5-ae67-f33488e4ea0d	2026-02-13 16:34:47.052877+05:30	2026-02-13 16:34:47.062776+05:30	\N
refund.processed	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1770898473, "entity": "event", "event": "refund.processed", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "375830622793", "upi_transaction_id": "284E244EA3BEB9A196163B5DE13D6F5D"}, "amount": 1000000, "amount_refunded": 1000000, "amount_transferred": 0, "bank": null, "base_amount": 1000000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1770898428, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 23600, "id": "pay_SFEL8CMrp7lO92", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "34856fa9-e02f-47f0-8550-a7d499e319f7"}, "order_id": "order_SFEKILybdhWGm0", "refund_status": "full", "status": "refunded", "tax": 3600, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 1000000, "batch_id": null, "created_at": 1770898470, "currency": "INR", "entity": "refund", "id": "rfnd_SFELsdLUWlfufl", "notes": [], "payment_id": "pay_SFEL8CMrp7lO92", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFEMQbupRU11va	t	808697b7-f751-4331-bd42-ba331d17430d	2026-02-13 16:34:47.5559+05:30	2026-02-13 16:34:47.560645+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFx3Kk7xRIuxTh", "entity": "payment", "amount": 350000, "currency": "INR", "status": "authorized", "order_id": "order_SFx39DOQ8DpvNH", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "920a5d08-8757-4ab0-ad92-a814a1ff65bd"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "135717986816", "upi_transaction_id": "06185F394B9B657E842BE03F89785258"}, "created_at": 1771055889, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771055890}	SFx3LbNwy6o4OI	t	30530a10-d5a6-44ff-84ca-9890077373cb	2026-02-14 13:28:21.107519+05:30	2026-02-14 13:28:21.117268+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SFx3Kk7xRIuxTh", "entity": "payment", "amount": 350000, "currency": "INR", "status": "captured", "order_id": "order_SFx39DOQ8DpvNH", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "920a5d08-8757-4ab0-ad92-a814a1ff65bd"}, "fee": 8260, "tax": 1260, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "135717986816", "upi_transaction_id": "06185F394B9B657E842BE03F89785258"}, "created_at": 1771055889, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 350000}}}, "created_at": 1771055890}	SFx3MDV0cR5TWG	t	b78414bf-b850-44f3-b05f-f4030ed37ff0	2026-02-14 13:28:21.164605+05:30	2026-02-14 13:28:21.259068+05:30	\N
refund.created	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1771054459, "entity": "event", "event": "refund.created", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "340348433630", "upi_transaction_id": "F7BBB5C21C6F1651AE53BB81A6975619"}, "amount": 350000, "amount_refunded": 350000, "amount_transferred": 0, "bank": null, "base_amount": 350000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1770977047, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 8260, "id": "pay_SFafHG6SlAt050", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "396b716f-117f-4f1b-8551-a6d6ba7353f3"}, "order_id": "order_SFaf8PgAp2NYQP", "refund_status": "full", "status": "refunded", "tax": 1260, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 350000, "batch_id": null, "created_at": 1771054455, "currency": "INR", "entity": "refund", "id": "rfnd_SFwe5XXkNzTS5w", "notes": [], "payment_id": "pay_SFafHG6SlAt050", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFwedbb7pDOGE2	t	9171e504-4f9d-46ea-8bde-1ca5c3b238b6	2026-02-14 13:28:54.905456+05:30	2026-02-14 13:28:54.908839+05:30	\N
refund.processed	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1771054459, "entity": "event", "event": "refund.processed", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "340348433630", "upi_transaction_id": "F7BBB5C21C6F1651AE53BB81A6975619"}, "amount": 350000, "amount_refunded": 350000, "amount_transferred": 0, "bank": null, "base_amount": 350000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1770977047, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 8260, "id": "pay_SFafHG6SlAt050", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "396b716f-117f-4f1b-8551-a6d6ba7353f3"}, "order_id": "order_SFaf8PgAp2NYQP", "refund_status": "full", "status": "refunded", "tax": 1260, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 350000, "batch_id": null, "created_at": 1771054455, "currency": "INR", "entity": "refund", "id": "rfnd_SFwe5XXkNzTS5w", "notes": [], "payment_id": "pay_SFafHG6SlAt050", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFweddU4qCan5v	t	1278c39a-2aac-42eb-878e-4c157568d51f	2026-02-14 13:28:54.936788+05:30	2026-02-14 13:28:54.940667+05:30	\N
refund.created	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1771055958, "entity": "event", "event": "refund.created", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "135717986816", "upi_transaction_id": "06185F394B9B657E842BE03F89785258"}, "amount": 350000, "amount_refunded": 350000, "amount_transferred": 0, "bank": null, "base_amount": 350000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1771055889, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 8260, "id": "pay_SFx3Kk7xRIuxTh", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "920a5d08-8757-4ab0-ad92-a814a1ff65bd"}, "order_id": "order_SFx39DOQ8DpvNH", "refund_status": "full", "status": "refunded", "tax": 1260, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 350000, "batch_id": null, "created_at": 1771055953, "currency": "INR", "entity": "refund", "id": "rfnd_SFx4SyavkDaNDT", "notes": [], "payment_id": "pay_SFx3Kk7xRIuxTh", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFx513exng3a1c	t	da4922e2-54e9-4316-8ae3-5157b90a5da9	2026-02-14 13:29:45.021057+05:30	2026-02-14 13:29:45.025496+05:30	\N
refund.processed	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1771055958, "entity": "event", "event": "refund.processed", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "135717986816", "upi_transaction_id": "06185F394B9B657E842BE03F89785258"}, "amount": 350000, "amount_refunded": 350000, "amount_transferred": 0, "bank": null, "base_amount": 350000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1771055889, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 8260, "id": "pay_SFx3Kk7xRIuxTh", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "920a5d08-8757-4ab0-ad92-a814a1ff65bd"}, "order_id": "order_SFx39DOQ8DpvNH", "refund_status": "full", "status": "refunded", "tax": 1260, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 350000, "batch_id": null, "created_at": 1771055953, "currency": "INR", "entity": "refund", "id": "rfnd_SFx4SyavkDaNDT", "notes": [], "payment_id": "pay_SFx3Kk7xRIuxTh", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SFx514xOVb4I1L	t	444bbc44-55e0-4a8d-b519-f7929d2d4453	2026-02-14 13:29:45.045743+05:30	2026-02-14 13:29:45.050056+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SGPoj0rRl6Tngc", "entity": "payment", "amount": 110000, "currency": "INR", "status": "authorized", "order_id": "order_SGPoYnjGkeD4NN", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "ffbf59bd-6bb8-4c1d-83ec-5810e5e40209"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "596238193909", "upi_transaction_id": "A1879D3F3701CACAD70273E709281902"}, "created_at": 1771157186, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771157187}	SGPojwQ1I0WHzS	t	2f29a5d0-754f-4276-ba84-f5208459e541	2026-02-15 17:37:09.547047+05:30	2026-02-15 17:37:09.560326+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SGPoj0rRl6Tngc", "entity": "payment", "amount": 110000, "currency": "INR", "status": "captured", "order_id": "order_SGPoYnjGkeD4NN", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "ffbf59bd-6bb8-4c1d-83ec-5810e5e40209"}, "fee": 2596, "tax": 396, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "596238193909", "upi_transaction_id": "A1879D3F3701CACAD70273E709281902"}, "created_at": 1771157186, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 110000}}}, "created_at": 1771157187}	SGPokYsGUOgQr6	t	9fb61619-36da-45a9-9b38-1d0dc92160fd	2026-02-15 17:37:09.560745+05:30	2026-02-15 17:37:09.656179+05:30	\N
refund.processed	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1771164720, "entity": "event", "event": "refund.processed", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "596238193909", "upi_transaction_id": "A1879D3F3701CACAD70273E709281902"}, "amount": 110000, "amount_refunded": 110000, "amount_transferred": 0, "bank": null, "base_amount": 110000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1771157186, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 2596, "id": "pay_SGPoj0rRl6Tngc", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "ffbf59bd-6bb8-4c1d-83ec-5810e5e40209"}, "order_id": "order_SGPoYnjGkeD4NN", "refund_status": "full", "status": "refunded", "tax": 396, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 110000, "batch_id": null, "created_at": 1771164717, "currency": "INR", "entity": "refund", "id": "rfnd_SGRxIo45GXVnPP", "notes": [], "payment_id": "pay_SGPoj0rRl6Tngc", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SGRxqlLIlLWslN	t	59d3a81f-2871-4691-97ad-0332aeabae55	2026-02-15 19:42:28.178283+05:30	2026-02-15 19:42:28.245156+05:30	\N
refund.created	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1771164720, "entity": "event", "event": "refund.created", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "596238193909", "upi_transaction_id": "A1879D3F3701CACAD70273E709281902"}, "amount": 110000, "amount_refunded": 110000, "amount_transferred": 0, "bank": null, "base_amount": 110000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1771157186, "currency": "INR", "description": "Booking for Property b4eedd5d-fc61-46d9-8e03-42b94f8137e0", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 2596, "id": "pay_SGPoj0rRl6Tngc", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "ffbf59bd-6bb8-4c1d-83ec-5810e5e40209"}, "order_id": "order_SGPoYnjGkeD4NN", "refund_status": "full", "status": "refunded", "tax": 396, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 110000, "batch_id": null, "created_at": 1771164717, "currency": "INR", "entity": "refund", "id": "rfnd_SGRxIo45GXVnPP", "notes": [], "payment_id": "pay_SGPoj0rRl6Tngc", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SGRxqmdbbcRPIC	t	e3931447-ac50-4d7e-9c6a-319a0383ff33	2026-02-15 19:42:28.253136+05:30	2026-02-15 19:42:28.26161+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SGkkE92dZqNcmh", "entity": "payment", "amount": 550000, "currency": "INR", "status": "authorized", "order_id": "order_SGkk2iQ8JNLc2C", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "377d2fc5-57f5-4cb8-8bdc-0840110abc45"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "229661315180", "upi_transaction_id": "EC319B55F8C6F5462E1ADFD6F1D688FC"}, "created_at": 1771230885, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771230885}	SGkkF3jNLAjw9y	t	01e2533d-df49-45c5-bf2d-1b278a4bc095	2026-02-16 14:04:57.238547+05:30	2026-02-16 14:04:57.246285+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SGkkE92dZqNcmh", "entity": "payment", "amount": 550000, "currency": "INR", "status": "captured", "order_id": "order_SGkk2iQ8JNLc2C", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "377d2fc5-57f5-4cb8-8bdc-0840110abc45"}, "fee": 12980, "tax": 1980, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "229661315180", "upi_transaction_id": "EC319B55F8C6F5462E1ADFD6F1D688FC"}, "created_at": 1771230885, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 550000}}}, "created_at": 1771230886}	SGkkFhZYdDRHnG	t	ef266309-4160-463f-b7f0-b997cd274bcc	2026-02-16 14:05:01.617079+05:30	2026-02-16 14:05:01.64222+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SGpQzCaRvg7b8L", "entity": "payment", "amount": 110000, "currency": "INR", "status": "authorized", "order_id": "order_SGpQoLCkRnZ1u1", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "eb6436cf-0c2b-4ba8-b0a3-3ed98c96dd32"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "260732951029", "upi_transaction_id": "D6D2FB5E37A0D66D6566BFE9A34B177D"}, "created_at": 1771247400, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771247400}	SGpR0B6VOGzQQC	t	e79e6041-203a-470b-8bb0-a043cc960b06	2026-02-16 18:40:01.115247+05:30	2026-02-16 18:40:01.125425+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SGpQzCaRvg7b8L", "entity": "payment", "amount": 110000, "currency": "INR", "status": "captured", "order_id": "order_SGpQoLCkRnZ1u1", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "eb6436cf-0c2b-4ba8-b0a3-3ed98c96dd32"}, "fee": 2596, "tax": 396, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "260732951029", "upi_transaction_id": "D6D2FB5E37A0D66D6566BFE9A34B177D"}, "created_at": 1771247400, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 110000}}}, "created_at": 1771247401}	SGpR0sRdy7U0BT	t	8811d9ac-553f-46b7-95ac-c79dc04556d5	2026-02-16 18:40:01.720169+05:30	2026-02-16 18:40:01.74984+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SH9wy5agswS2ze", "entity": "payment", "amount": 165000, "currency": "INR", "status": "authorized", "order_id": "order_SH9wnv3G2N2zuX", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "daf5d818-5622-4d7c-9043-22e0cc392100"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "669625092099", "upi_transaction_id": "88AF2E9AF28D3B6FEFED0D3020F9824D"}, "created_at": 1771319649, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771319649}	SH9wz1F6ZXKpU5	t	6679d624-e8c2-4064-b203-d467216215ea	2026-02-17 14:44:10.027544+05:30	2026-02-17 14:44:10.036395+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SH9wy5agswS2ze", "entity": "payment", "amount": 165000, "currency": "INR", "status": "captured", "order_id": "order_SH9wnv3G2N2zuX", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "daf5d818-5622-4d7c-9043-22e0cc392100"}, "fee": 3894, "tax": 594, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "669625092099", "upi_transaction_id": "88AF2E9AF28D3B6FEFED0D3020F9824D"}, "created_at": 1771319649, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 165000}}}, "created_at": 1771319650}	SH9wzgVleholI5	t	97a709b9-6647-4bd3-8ab1-aaabaa0a21d2	2026-02-17 14:44:10.54484+05:30	2026-02-17 14:44:10.571035+05:30	\N
refund.processed	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1771324272, "entity": "event", "event": "refund.processed", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "669625092099", "upi_transaction_id": "88AF2E9AF28D3B6FEFED0D3020F9824D"}, "amount": 165000, "amount_refunded": 165000, "amount_transferred": 0, "bank": null, "base_amount": 165000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1771319649, "currency": "INR", "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 3894, "id": "pay_SH9wy5agswS2ze", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "daf5d818-5622-4d7c-9043-22e0cc392100"}, "order_id": "order_SH9wnv3G2N2zuX", "refund_status": "full", "status": "refunded", "tax": 594, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 165000, "batch_id": null, "created_at": 1771324269, "currency": "INR", "entity": "refund", "id": "rfnd_SHBGJCGsaluMou", "notes": [], "payment_id": "pay_SH9wy5agswS2ze", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SHBGr9KflYQqx9	t	12259434-d477-4989-9e66-1cbd5cfbd2be	2026-02-17 16:01:40.424912+05:30	2026-02-17 16:01:40.432188+05:30	\N
refund.created	{"account_id": "acc_S7Dlaw8LNbaM6o", "contains": ["refund", "payment"], "created_at": 1771324272, "entity": "event", "event": "refund.created", "payload": {"payment": {"entity": {"acquirer_data": {"rrn": "669625092099", "upi_transaction_id": "88AF2E9AF28D3B6FEFED0D3020F9824D"}, "amount": 165000, "amount_refunded": 165000, "amount_transferred": 0, "bank": null, "base_amount": 165000, "captured": true, "card_id": null, "contact": "+917073118909", "created_at": 1771319649, "currency": "INR", "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "email": "super_admin@yopmail.com", "entity": "payment", "error_code": null, "error_description": null, "error_reason": null, "error_source": null, "error_step": null, "fee": 3894, "id": "pay_SH9wy5agswS2ze", "international": false, "invoice_id": null, "method": "upi", "notes": {"booking_id": "daf5d818-5622-4d7c-9043-22e0cc392100"}, "order_id": "order_SH9wnv3G2N2zuX", "refund_status": "full", "status": "refunded", "tax": 594, "upi": {"flow": "collect", "vpa": "success@razorpay"}, "vpa": "success@razorpay", "wallet": null}}, "refund": {"entity": {"acquirer_data": {"rrn": "10000000000000"}, "amount": 165000, "batch_id": null, "created_at": 1771324269, "currency": "INR", "entity": "refund", "id": "rfnd_SHBGJCGsaluMou", "notes": [], "payment_id": "pay_SH9wy5agswS2ze", "receipt": null, "speed_processed": "normal", "speed_requested": "normal", "status": "processed"}}}}	SHBGrA2HqKaUY7	t	353a2957-0c43-4cf8-ac2c-c1e042008f3e	2026-02-17 16:01:40.447292+05:30	2026-02-17 16:01:40.450065+05:30	\N
payment.failed	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.failed", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHByH4BgfgP71r", "entity": "payment", "amount": 495000, "currency": "INR", "status": "failed", "order_id": "order_SHBxgOX8SiFsng", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "failure@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "13a8edb2-769f-4eb1-8c61-3c691fa78f30"}, "fee": null, "tax": null, "error_code": "BAD_REQUEST_ERROR", "error_description": "Payment was unsuccessful due to a temporary issue. If amount got deducted, it will be refunded within 5-7 working days.", "error_source": "gateway", "error_step": "payment_response", "error_reason": "payment_failed", "acquirer_data": {"rrn": null}, "created_at": 1771326766, "upi": {"vpa": "failure@razorpay", "flow": "collect"}}}}, "created_at": 1771326767}	SHByIKe68SDiuf	t	7bcf51a0-d9b3-4068-9bda-e452c8c063d6	2026-02-17 16:42:47.756747+05:30	2026-02-17 16:42:47.779292+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHCj7lgubtPbqx", "entity": "payment", "amount": 110000, "currency": "INR", "status": "authorized", "order_id": "order_SHCj0AMFBWvDa5", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property 40423840-4cfc-483d-8dc2-30dbd61135d3", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "55b81660-7973-4db8-907b-21bb85414f8d"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "307004513227", "upi_transaction_id": "46F25ECC40BEC51262AB760FF40ED6B4"}, "created_at": 1771329427, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771329428}	SHCj8i9RWqTFzk	t	a80ac9ac-8e75-4dd5-9b21-52ba4bd59a00	2026-02-17 17:27:08.443785+05:30	2026-02-17 17:27:08.45094+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHCj7lgubtPbqx", "entity": "payment", "amount": 110000, "currency": "INR", "status": "captured", "order_id": "order_SHCj0AMFBWvDa5", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property 40423840-4cfc-483d-8dc2-30dbd61135d3", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "55b81660-7973-4db8-907b-21bb85414f8d"}, "fee": 2596, "tax": 396, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "307004513227", "upi_transaction_id": "46F25ECC40BEC51262AB760FF40ED6B4"}, "created_at": 1771329427, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 110000}}}, "created_at": 1771329428}	SHCj9OACQorzZM	t	0f0c0516-a64f-467c-9af4-b3d03531cb73	2026-02-17 17:27:09.093884+05:30	2026-02-17 17:27:09.122929+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHHcsxatG9Q6x7", "entity": "payment", "amount": 110000, "currency": "INR", "status": "authorized", "order_id": "order_SHHch1XC9Hlg17", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property 40423840-4cfc-483d-8dc2-30dbd61135d3", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "c6660d19-e647-4e4d-afe5-c741f139de5a"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "380759406485", "upi_transaction_id": "E9B97F0D4B909DCB088A46D67363D2EA"}, "created_at": 1771346681, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771346681}	SHHctqvaLQKd0f	t	6d7ec063-c7b0-4c83-b2e0-6df1c474e7fc	2026-02-17 22:14:42.074948+05:30	2026-02-17 22:14:42.082816+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHHcsxatG9Q6x7", "entity": "payment", "amount": 110000, "currency": "INR", "status": "captured", "order_id": "order_SHHch1XC9Hlg17", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property 40423840-4cfc-483d-8dc2-30dbd61135d3", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "c6660d19-e647-4e4d-afe5-c741f139de5a"}, "fee": 2596, "tax": 396, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "380759406485", "upi_transaction_id": "E9B97F0D4B909DCB088A46D67363D2EA"}, "created_at": 1771346681, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 110000}}}, "created_at": 1771346682}	SHHcuVHmFcxTpn	t	4c6f39c3-ee7d-44f3-a8da-b5edd8a91459	2026-02-17 22:14:42.707399+05:30	2026-02-17 22:14:42.731813+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHVWekodXFVFBy", "entity": "payment", "amount": 440000, "currency": "INR", "status": "authorized", "order_id": "order_SHVWTZPhSs6ACT", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "e8f684c2-4969-49ce-a8d4-1df49ab8029a"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "980120211601", "upi_transaction_id": "40AE7E61A6CD373BFDBB9BF724142782"}, "created_at": 1771395630, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771395630}	SHVWfe5zl0rK0U	t	9d2743d2-0b9d-44ba-9c86-11d0467a1f8c	2026-02-18 11:50:30.882156+05:30	2026-02-18 11:50:30.8955+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHVWekodXFVFBy", "entity": "payment", "amount": 440000, "currency": "INR", "status": "captured", "order_id": "order_SHVWTZPhSs6ACT", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "e8f684c2-4969-49ce-a8d4-1df49ab8029a"}, "fee": 10384, "tax": 1584, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "980120211601", "upi_transaction_id": "40AE7E61A6CD373BFDBB9BF724142782"}, "created_at": 1771395630, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 440000}}}, "created_at": 1771395631}	SHVWgFHFBCNbey	t	861ab5e4-12d0-43e8-b8d7-2f3071863d6f	2026-02-18 11:50:31.497299+05:30	2026-02-18 11:50:31.521703+05:30	\N
payment.authorized	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.authorized", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHbFtmFCFRQC6T", "entity": "payment", "amount": 440000, "currency": "INR", "status": "authorized", "order_id": "order_SHbFhyDxHiSGVA", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": false, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "09275936-0907-413f-805e-5928905b8ce3"}, "fee": null, "tax": null, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "936409565361", "upi_transaction_id": "9F197021ACB20FF71C8A2DFFB73FB555"}, "created_at": 1771415808, "upi": {"vpa": "success@razorpay", "flow": "collect"}}}}, "created_at": 1771415808}	SHbFuleLhixgPp	t	29ec45bc-1415-4930-95dc-213084fed8b7	2026-02-18 17:26:48.757622+05:30	2026-02-18 17:26:48.76616+05:30	\N
payment.captured	{"entity": "event", "account_id": "acc_S7Dlaw8LNbaM6o", "event": "payment.captured", "contains": ["payment"], "payload": {"payment": {"entity": {"id": "pay_SHbFtmFCFRQC6T", "entity": "payment", "amount": 440000, "currency": "INR", "status": "captured", "order_id": "order_SHbFhyDxHiSGVA", "invoice_id": null, "international": false, "method": "upi", "amount_refunded": 0, "refund_status": null, "captured": true, "description": "Booking for Property c30f5707-5e50-4c4f-afe5-36dfae9a46ff", "card_id": null, "bank": null, "wallet": null, "vpa": "success@razorpay", "email": "super_admin@yopmail.com", "contact": "+917073118909", "notes": {"booking_id": "09275936-0907-413f-805e-5928905b8ce3"}, "fee": 10384, "tax": 1584, "error_code": null, "error_description": null, "error_source": null, "error_step": null, "error_reason": null, "acquirer_data": {"rrn": "936409565361", "upi_transaction_id": "9F197021ACB20FF71C8A2DFFB73FB555"}, "created_at": 1771415808, "reward": null, "upi": {"vpa": "success@razorpay", "flow": "collect"}, "base_amount": 440000}}}, "created_at": 1771415809}	SHbFvOfy5Nnl7X	t	a0d2c773-54bd-4488-ab09-d8dec53fd7c8	2026-02-18 17:26:49.295508+05:30	2026-02-18 17:26:49.317946+05:30	\N
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: amenities amenities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.amenities
    ADD CONSTRAINT amenities_pkey PRIMARY KEY (id);


--
-- Name: blacklisted_tokens blacklisted_tokens_jti_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_jti_key UNIQUE (jti);


--
-- Name: blacklisted_tokens blacklisted_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_pkey PRIMARY KEY (id);


--
-- Name: bookings bookings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: payments payments_razorpay_order_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_razorpay_order_id_key UNIQUE (razorpay_order_id);


--
-- Name: properties properties_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT properties_pkey PRIMARY KEY (id);


--
-- Name: property_amenities property_amenities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.property_amenities
    ADD CONSTRAINT property_amenities_pkey PRIMARY KEY (property_id, amenity_id, id);


--
-- Name: property_images property_images_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.property_images
    ADD CONSTRAINT property_images_pkey PRIMARY KEY (id);


--
-- Name: reviews reviews_booking_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_booking_id_key UNIQUE (booking_id);


--
-- Name: reviews reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (id);


--
-- Name: tenants tenants_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_name_key UNIQUE (name);


--
-- Name: tenants tenants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tenants
    ADD CONSTRAINT tenants_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: webhooks webhooks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.webhooks
    ADD CONSTRAINT webhooks_pkey PRIMARY KEY (id);


--
-- Name: webhooks webhooks_razorpay_event_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.webhooks
    ADD CONSTRAINT webhooks_razorpay_event_id_key UNIQUE (razorpay_event_id);


--
-- Name: ix_blacklisted_tokens_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_blacklisted_tokens_user_id ON public.blacklisted_tokens USING btree (user_id);


--
-- Name: ix_bookings_check_in; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookings_check_in ON public.bookings USING btree (check_in);


--
-- Name: ix_bookings_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookings_created_at ON public.bookings USING btree (created_at);


--
-- Name: ix_bookings_guest_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookings_guest_id ON public.bookings USING btree (guest_id);


--
-- Name: ix_bookings_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookings_property_id ON public.bookings USING btree (property_id);


--
-- Name: ix_bookings_property_manager_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookings_property_manager_id ON public.bookings USING btree (property_manager_id);


--
-- Name: ix_bookings_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookings_status ON public.bookings USING btree (status);


--
-- Name: ix_bookings_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookings_tenant_id ON public.bookings USING btree (tenant_id);


--
-- Name: ix_bookings_tenant_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_bookings_tenant_status ON public.bookings USING btree (tenant_id, status);


--
-- Name: ix_messages_booking_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_messages_booking_id ON public.messages USING btree (booking_id);


--
-- Name: ix_messages_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_messages_tenant_id ON public.messages USING btree (tenant_id);


--
-- Name: ix_payments_booking_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_booking_id ON public.payments USING btree (booking_id);


--
-- Name: ix_payments_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_created_at ON public.payments USING btree (created_at);


--
-- Name: ix_payments_guest_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_guest_id ON public.payments USING btree (guest_id);


--
-- Name: ix_payments_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_status ON public.payments USING btree (status);


--
-- Name: ix_payments_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_tenant_id ON public.payments USING btree (tenant_id);


--
-- Name: ix_payments_tenant_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_payments_tenant_status ON public.payments USING btree (tenant_id, status);


--
-- Name: ix_properties_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_properties_category ON public.properties USING btree (category);


--
-- Name: ix_properties_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_properties_city ON public.properties USING btree (city);


--
-- Name: ix_properties_managed_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_properties_managed_by ON public.properties USING btree (managed_by);


--
-- Name: ix_properties_price_per_night; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_properties_price_per_night ON public.properties USING btree (price_per_night);


--
-- Name: ix_properties_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_properties_tenant_id ON public.properties USING btree (tenant_id);


--
-- Name: ix_property_images_property_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_property_images_property_id ON public.property_images USING btree (property_id);


--
-- Name: ix_reviews_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_reviews_tenant_id ON public.reviews USING btree (tenant_id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_tenant_id ON public.users USING btree (tenant_id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: ix_webhooks_tenant_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_webhooks_tenant_id ON public.webhooks USING btree (tenant_id);


--
-- Name: uq_amenity_name_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_amenity_name_active ON public.amenities USING btree (name) WHERE (is_deleted IS FALSE);


--
-- Name: uq_tenant_email_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_tenant_email_active ON public.users USING btree (tenant_id, email) WHERE (is_deleted IS FALSE);


--
-- Name: uq_tenant_username_active; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_tenant_username_active ON public.users USING btree (tenant_id, username) WHERE (is_deleted IS FALSE);


--
-- Name: blacklisted_tokens blacklisted_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blacklisted_tokens
    ADD CONSTRAINT blacklisted_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: bookings bookings_guest_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_guest_id_fkey FOREIGN KEY (guest_id) REFERENCES public.users(id);


--
-- Name: bookings bookings_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id);


--
-- Name: bookings bookings_property_manager_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_property_manager_id_fkey FOREIGN KEY (property_manager_id) REFERENCES public.users(id);


--
-- Name: bookings bookings_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bookings
    ADD CONSTRAINT bookings_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: messages messages_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id) ON DELETE CASCADE;


--
-- Name: messages messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- Name: messages messages_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: payments payments_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id);


--
-- Name: payments payments_guest_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_guest_id_fkey FOREIGN KEY (guest_id) REFERENCES public.users(id);


--
-- Name: payments payments_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: properties properties_managed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT properties_managed_by_fkey FOREIGN KEY (managed_by) REFERENCES public.users(id);


--
-- Name: properties properties_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.properties
    ADD CONSTRAINT properties_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: property_amenities property_amenities_amenity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.property_amenities
    ADD CONSTRAINT property_amenities_amenity_id_fkey FOREIGN KEY (amenity_id) REFERENCES public.amenities(id) ON DELETE CASCADE;


--
-- Name: property_amenities property_amenities_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.property_amenities
    ADD CONSTRAINT property_amenities_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE;


--
-- Name: property_images property_images_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.property_images
    ADD CONSTRAINT property_images_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id) ON DELETE CASCADE;


--
-- Name: reviews reviews_booking_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_booking_id_fkey FOREIGN KEY (booking_id) REFERENCES public.bookings(id);


--
-- Name: reviews reviews_guest_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_guest_id_fkey FOREIGN KEY (guest_id) REFERENCES public.users(id);


--
-- Name: reviews reviews_property_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_property_id_fkey FOREIGN KEY (property_id) REFERENCES public.properties(id);


--
-- Name: reviews reviews_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- Name: users users_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id);


--
-- Name: webhooks webhooks_tenant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.webhooks
    ADD CONSTRAINT webhooks_tenant_id_fkey FOREIGN KEY (tenant_id) REFERENCES public.tenants(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict vObos2r1fedzK3qAVZ3PKW4gI3OxHofx77lkqZ47qsJV2R1QEFerviDr6jPB6Zg

