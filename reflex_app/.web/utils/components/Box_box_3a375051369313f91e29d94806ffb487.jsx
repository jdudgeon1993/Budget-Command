
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_3a375051369313f91e29d94806ffb487 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_5c3cf139fcdc91fff79f6df506137e4c = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.do_reopen_month", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#FF9F0A", ["cursor"] : "pointer", ["padding"] : "5px 10px", ["borderRadius"] : "6px", ["border"] : "1px solid #FF9F0A44", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["&:hover"] : ({ ["background"] : "#FF9F0A0d" }) }),onClick:on_click_5c3cf139fcdc91fff79f6df506137e4c},children)
    )
});
