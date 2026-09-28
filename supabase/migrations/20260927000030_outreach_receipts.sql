-- Opening an external composer and confirming a send are distinct user actions.
ALTER TABLE public.relationship_actions DROP CONSTRAINT relationship_actions_action_check;
ALTER TABLE public.relationship_actions ADD CONSTRAINT relationship_actions_action_check
 CHECK(action IN ('completed','scheduled','dismissed','opened','sent'));
