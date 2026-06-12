
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_47407b0880b1f96352cccd86bc504e3e = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_c1b59a307c088b31099201cd19969200 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_edit_paycheck", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 16px", ["borderRadius"] : "8px", ["border"] : "1px solid #252535", ["color"] : "#8282a2", ["fontSize"] : "12px", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["&:hover"] : ({ ["background"] : "#1c1c25" }) }),onClick:on_click_c1b59a307c088b31099201cd19969200},children)
    )
});
