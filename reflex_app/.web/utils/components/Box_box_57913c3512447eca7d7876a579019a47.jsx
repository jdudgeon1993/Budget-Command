
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_57913c3512447eca7d7876a579019a47 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_bbe1f602aca07fe0e36fbc448507e783 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.do_close_month", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#6868a2", ["cursor"] : "pointer", ["padding"] : "5px 10px", ["borderRadius"] : "6px", ["border"] : "1px solid #252535", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["&:hover"] : ({ ["color"] : "#8282a2", ["borderColor"] : "#3c3c56" }) }),onClick:on_click_bbe1f602aca07fe0e36fbc448507e783},children)
    )
});
